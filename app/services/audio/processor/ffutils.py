# app/services/audio/processor/ffutils.py
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from app.core.config import (
    SAMPLE_RATE as TARGET_SAMPLE_RATE,
    TARGET_CHANNELS,
    TARGET_BIT_DEPTH,
    TARGET_CONTAINER,
    TARGET_CODEC,
)
from .audio_meta import AudioMeta


# -------- Public API --------
def ensure_ffmpeg_tools() -> None:
    """Ensure ffmpeg & ffprobe exist in PATH."""
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("ffmpeg/ffprobe not found in PATH. Please install ffmpeg.")


def probe_format(path: Path) -> AudioMeta:
    """Return lightweight metadata for an audio file using ffprobe."""
    ensure_ffmpeg_tools()
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_streams",
        "-show_format",
        "-print_format", "json",
        str(path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed:\n{proc.stderr.decode(errors='ignore')}")

    info = json.loads(proc.stdout.decode("utf-8", errors="ignore"))
    stream = _pick_audio_stream(info)
    fmt = info.get("format", {}) or {}

    codec = stream.get("codec_name") or ""
    channels = int(stream.get("channels") or 0)
    sample_rate = int(_safe_int(stream.get("sample_rate")) or 0)
    sample_fmt = (stream.get("sample_fmt") or "").lower()
    bit_depth = _bit_depth_from_sample_fmt(sample_fmt)
    duration_sec = float(fmt.get("duration") or 0.0)
    container_full = (fmt.get("format_name") or "").lower()
    container = container_full.split(",")[0] if container_full else ""

    return AudioMeta(
        path=str(path),
        container=container,
        codec=codec,
        sample_rate=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        duration_sec=duration_sec,
        was_converted=False,
        reason=None,
    )


def needs_pcm16_mono_16k(meta: AudioMeta) -> bool:
    """Decide if conversion to WAV PCM s16le mono 16k is required."""
    if (meta["container"] != TARGET_CONTAINER
        or meta["codec"] != TARGET_CODEC
        or meta["channels"] != TARGET_CHANNELS
        or meta["sample_rate"] != TARGET_SAMPLE_RATE):
        return True
    # Some WAVs can be pcm_s24le/32f; enforce 16-bit if known
    if meta["bit_depth"] is not None and meta["bit_depth"] != TARGET_BIT_DEPTH:
        return True
    return False


def convert_to_pcm16_mono_16k(src: Path) -> Path:
    """
    Convert audio to WAV PCM s16le, mono, 16kHz using ffmpeg.
    Returns the path to the converted file.
    """
    ensure_ffmpeg_tools()
    dst = src.with_name(src.stem + "_fixed.wav")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-vn", "-sn", "-dn",          # drop video/subtitles/data if present
        "-ac", str(TARGET_CHANNELS),  # mono
        "-ar", str(TARGET_SAMPLE_RATE),       # 16 kHz
        "-sample_fmt", "s16",          # PCM 16-bit
        str(dst),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr.decode(errors='ignore')}")
    return dst


# -------- Internals --------
def _pick_audio_stream(info: dict) -> dict:
    streams = info.get("streams") or []
    for s in streams:
        if s.get("codec_type") == "audio":
            return s
    return {}

def _bit_depth_from_sample_fmt(sample_fmt: str) -> Optional[int]:
    """
    Map ffprobe sample_fmt → bit depth where applicable.
    For compressed formats (mp3/aac/opus/...), ffprobe often omits or uses 'fltp' etc. Return None.
    """
    mapping = {
        "s16": 16, "s16p": 16,
        "s24": 24, "s24p": 24,
        "s32": 32, "s32p": 32,
        "s64": 64, "s64p": 64,
        "u8": 8, "u8p": 8,
        "s8": 8, "s8p": 8,
        "flt": None, "fltp": None,      # float → not fixed PCM bit-depth
        "dbl": None, "dblp": None,
    }
    return mapping.get(sample_fmt, None)

def _safe_int(val) -> Optional[int]:
    try:
        return int(val)
    except Exception:
        return None

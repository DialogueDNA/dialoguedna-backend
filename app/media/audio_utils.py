# app/media/audio_utils.py

from __future__ import annotations
from pathlib import Path
from typing import Dict
from uuid import uuid4
from pydub import AudioSegment
from fastapi import UploadFile

from app.core.config import (
    SAMPLE_RATE, TARGET_CHANNELS, TARGET_BIT_DEPTH,
    TARGET_CONTAINER, TARGET_CODEC,
)

# Visible folders for debugging
RAW_DIR = Path("temp_converted_audio_file/src")
CONVERTED_DIR = Path("temp_converted_audio_file/converted")
RAW_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)


def save_upload_to_visible_tmp(file: UploadFile) -> Path:
    """
    Save the original uploaded file into a stable, visible folder (RAW_DIR).
    Returns the saved Path (preserves extension when possible).
    """
    # Try to preserve original extension if available
    orig_name = (file.filename or "upload")
    ext = Path(orig_name).suffix or ".bin"
    out_path = RAW_DIR / f"{Path(orig_name).stem}_{uuid4().hex[:8]}{ext}"

    # Ensure file pointer at start and copy
    file.file.seek(0)
    with open(out_path, "wb") as dst:
        dst.write(file.file.read())

    if not out_path.exists():
        raise FileNotFoundError(f"Raw file not saved: {out_path}")

    return out_path


def ensure_transcription_ready(src_path: Path) -> Path:
    """
    Ensure WAV, PCM s16, 16 kHz, mono. If already compliant, return src.
    Otherwise, write converted file into CONVERTED_DIR and return its Path.
    """
    src_path = Path(src_path)

    if _is_wav_pcm16_mono16k(src_path):
        return src_path
    if not src_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {src_path}")

    audio = AudioSegment.from_file(src_path)
    audio = (
        audio.set_frame_rate(int(SAMPLE_RATE))
             .set_channels(int(TARGET_CHANNELS))
             .set_sample_width(int(TARGET_BIT_DEPTH // 8))
    )

    out_name = f"{src_path.stem}_{uuid4().hex[:8]}_16k_mono.wav"
    out_path = CONVERTED_DIR / out_name
    audio.export(out_path, format=TARGET_CONTAINER)

    if not out_path.exists():
        raise FileNotFoundError(f"Converted file was not created: {out_path}")

    return out_path


def probe(path: Path) -> Dict[str, object]:
    """Basic audio properties for logging/verification."""
    path = Path(path)
    audio = AudioSegment.from_file(path)
    sample_rate = audio.frame_rate
    channels = audio.channels
    bit_depth = audio.sample_width * 8
    duration_sec = len(audio) / 1000.0
    container = path.suffix.lstrip(".").lower()
    codec = "pcm_s16le" if (container == "wav" and bit_depth == 16) else "unknown"
    return {
        "sample_rate": sample_rate,
        "channels": channels,
        "bit_depth": bit_depth,
        "duration_sec": duration_sec,
        "container": container,
        "codec": codec,
    }


def _is_wav_pcm16_mono16k(path: Path) -> bool:
    """Check: WAV container, 16-bit, mono, 16 kHz."""
    try:
        path = Path(path)
        if path.suffix.lower() != ".wav":
            return False
        audio = AudioSegment.from_file(path)
        return (
            audio.frame_rate == int(SAMPLE_RATE) and
            audio.channels == int(TARGET_CHANNELS) and
            audio.sample_width == int(TARGET_BIT_DEPTH // 8)
        )
    except Exception:
        return False

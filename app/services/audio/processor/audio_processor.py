# app/services/audio/processor/audio_processor.py
from __future__ import annotations
import tempfile
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

from app.core.config import (
    SAMPLE_RATE as TARGET_SAMPLE_RATE,
    TARGET_CHANNELS,
    TARGET_BIT_DEPTH,
    TARGET_CONTAINER,
    TARGET_CODEC,
)
from .audio_meta import AudioMeta
from .ffutils import (
    ensure_ffmpeg_tools,
    probe_format,
    needs_pcm16_mono_16k,
    convert_to_pcm16_mono_16k,
)


class AudioProcessor:
    """
    Prepares audio for transcription:
    - Save UploadFile to a local temp file
    - Probe format via ffprobe
    - Convert to WAV PCM16 mono 16k if required
    - Return (ready_path, metadata)
    """

    def __init__(self, temp_dir: Path | None = None) -> None:
        self.temp_dir = Path(temp_dir) if temp_dir else None

    # ---------- Public API ----------
    async def prepare(self, upload: UploadFile) -> Tuple[Path, AudioMeta]:
        """
        Accepts an UploadFile, writes it to a temp file, ensures target format,
        and returns (ready_path, meta).
        """
        if upload is None:
            raise ValueError("UploadFile must be provided.")

        ensure_ffmpeg_tools()
        src_path = await self._save_upload_to_temp(upload)
        return self.prepare_path(src_path)

    def prepare_path(self, local_path: Path) -> Tuple[Path, AudioMeta]:
        """
        Same as prepare(), but starts from an existing local file path.
        Useful for tests or when the file already exists on disk.
        """
        ensure_ffmpeg_tools()

        meta = probe_format(local_path)
        if needs_pcm16_mono_16k(meta):
            fixed = convert_to_pcm16_mono_16k(local_path)
            fixed_meta = probe_format(fixed)
            fixed_meta["was_converted"] = True
            fixed_meta["reason"] = _conversion_reason(meta)
            return fixed, fixed_meta

        # Already matches target
        meta["was_converted"] = False
        meta["reason"] = None
        return local_path, meta

    # ---------- Internals ----------
    async def _save_upload_to_temp(self, upload: UploadFile) -> Path:
        """
        Write UploadFile to a named temp file (preserve extension if present).
        """
        suffix = ""
        if upload.filename and "." in upload.filename:
            suffix = "." + upload.filename.rsplit(".", 1)[-1]

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=self._tmp_dir_str())
        try:
            # Stream to disk
            content = await upload.read()
            tmp.write(content)
        finally:
            tmp.close()
        return Path(tmp.name)

    def _tmp_dir_str(self) -> str | None:
        return str(self.temp_dir) if self.temp_dir else None


# ---------- helpers ----------
def _conversion_reason(meta: AudioMeta) -> str:
    reasons: list[str] = []
    if meta["container"] != TARGET_CONTAINER:
        reasons.append(f"container:{meta['container']}→{TARGET_CONTAINER}")
    if meta["codec"] != TARGET_CODEC:
        reasons.append(f"codec:{meta['codec']}→{TARGET_CODEC}")
    if meta["channels"] != TARGET_CHANNELS:
        reasons.append(f"channels:{meta['channels']}→{TARGET_CHANNELS}")
    if meta["sample_rate"] != TARGET_SAMPLE_RATE:
        reasons.append(f"sr:{meta['sample_rate']}→{TARGET_SAMPLE_RATE}")
    if meta["bit_depth"] is not None and meta["bit_depth"] != TARGET_BIT_DEPTH:
        reasons.append(f"bit_depth:{meta['bit_depth']}→{TARGET_BIT_DEPTH}")
    return ", ".join(reasons) if reasons else "normalized"

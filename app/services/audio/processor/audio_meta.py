# app/services/audio/processor/audio_meta.py
from __future__ import annotations
from typing import Optional, TypedDict
from app.core.config import (
    SAMPLE_RATE as TARGET_SAMPLE_RATE,
    TARGET_CHANNELS,
    TARGET_BIT_DEPTH,
    TARGET_CONTAINER,
    TARGET_CODEC,
)

class AudioMeta(TypedDict):
    """
    Lightweight metadata returned by probing an audio file.
    This is *not* a full schema—only fields we actually use in processing.
    """
    # File info
    path: str           # absolute/local path of the probed file
    container: str      # e.g., "wav", "mp3", "m4a"
    codec: str          # e.g., "pcm_s16le", "mp3", "aac"

    # Signal info
    sample_rate: int    # Hz
    channels: int       # 1 = mono, 2 = stereo, ...
    bit_depth: Optional[int]  # bits per sample (None if unknown/compressed)
    duration_sec: float # seconds (float)

    # Processing flags
    was_converted: bool # True if we converted the original file
    reason: Optional[str]  # why conversion was required (or None)



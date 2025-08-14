from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional, Literal

import app.core.environment as env


@dataclass(frozen=True)
class SepformerConfig:
    """
    Config for SpeechBrain SepFormer separator.

    Notes:
    - `model`: HF hub id or local path for the SepFormer checkpoint.
    - `device`: "cpu" or "cuda" (with optional ":0" etc.).
    - `cache_dir`: where model files are stored (use a writable, persistent path in containers).
    - `model_sample_rate`: sample rate the checkpoint expects (most public SepFormer models use 16_000 Hz).
    - `downmix_mode`: how to turn multichannel input into mono ("mean" | "left" | "right").
    - `chunk_sec`: chunk length (seconds) for long files (controls memory usage).
    - `hop_fraction`: overlap ratio between chunks (0.5 = 50% overlap).
    - `num_speakers`: force output to exactly N sources (trim/pad). Use None to keep model default.
    """

    # Required / primary
    model: str = env.SEPFORMER_MODEL_NAME
    device: str = env.DEVICE

    # Optional / advanced
    cache_dir: str = field(
        default_factory=lambda: getattr(
            env,
            "SEPFORMER_CACHE_DIR",
            os.path.join(os.path.expanduser("~"), ".cache", "speechbrain", "sepformer"),
        )
    )
    model_sample_rate: int = field(
        default_factory=lambda: getattr(env, "SEPFORMER_MODEL_SAMPLE_RATE", 16_000)
    )
    downmix_mode: Literal["mean", "left", "right"] = field(
        default_factory=lambda: getattr(env, "SEPFORMER_DOWNMIX_MODE", "mean")
    )
    chunk_sec: float = field(
        default_factory=lambda: getattr(env, "SEPFORMER_CHUNK_SEC", 12.0)
    )
    hop_fraction: float = field(
        default_factory=lambda: getattr(env, "SEPFORMER_HOP_FRACTION", 0.5)
    )
    num_speakers: Optional[int] = field(
        default_factory=lambda: getattr(env, "SEPFORMER_NUM_SPEAKERS", None)
    )

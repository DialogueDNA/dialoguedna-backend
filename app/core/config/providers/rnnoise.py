# app/core/config/providers/rnnoise.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

import app.core.environment as env

StrengthT = Literal["light", "medium", "strong"]


@dataclass(frozen=True)
class RNNoiseConfig:
    """
    Config for RNNoise denoiser.

    - enhancer_strength: amount of denoising to apply.
    - target_sample_rate: RNNoise expects 48 kHz; we resample to this rate by default.
    - enable_resample: set False only if you *guarantee* the input is already at target SR.
    - passes_*: number of RNNoise passes per strength (simple heuristic).
    - clamp_after: lightly clamp output to [-1, 1] to avoid inter-frame spikes.
    """
    enhancer_strength: StrengthT = field(
        default_factory=lambda: getattr(env, "RNNOISE_ENHANCER_STRENGTH", "medium")
    )
    target_sample_rate: int = field(
        default_factory=lambda: getattr(env, "RNNOISE_TARGET_SAMPLE_RATE", 48_000)
    )
    enable_resample: bool = field(
        default_factory=lambda: getattr(env, "RNNOISE_ENABLE_RESAMPLE", True)
    )
    passes_light: int = field(
        default_factory=lambda: getattr(env, "RNNOISE_PASSES_LIGHT", 1)
    )
    passes_medium: int = field(
        default_factory=lambda: getattr(env, "RNNOISE_PASSES_MEDIUM", 2)
    )
    passes_strong: int = field(
        default_factory=lambda: getattr(env, "RNNOISE_PASSES_STRONG", 3)
    )
    clamp_after: bool = field(
        default_factory=lambda: getattr(env, "RNNOISE_CLAMP_AFTER", True)
    )

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
        default_factory=lambda: env.RNNOISE_ENHANCER_STRENGTH
    )
    target_sample_rate: int = field(
        default_factory=lambda: env.RNNOISE_TARGET_SAMPLE_RATE
    )
    enable_resample: bool = field(
        default_factory=lambda: env.RNNOISE_ENABLE_RESAMPLE
    )
    passes_light: int = field(
        default_factory=lambda: env.RNNOISE_PASSES_LIGHT
    )
    passes_medium: int = field(
        default_factory=lambda: env.RNNOISE_PASSES_MEDIUM
    )
    passes_strong: int = field(
        default_factory=lambda: env.RNNOISE_PASSES_STRONG
    )
    clamp_after: bool = field(
        default_factory=lambda: env.RNNOISE_CLAMP_AFTER
    )

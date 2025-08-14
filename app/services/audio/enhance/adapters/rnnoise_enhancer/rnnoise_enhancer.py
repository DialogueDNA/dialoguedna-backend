from __future__ import annotations
import numpy as np
import torch
from typing import Literal

# Fallback to spectral gating if rnnoise is not available.
try:
    from pyrnnoise import RNNoise
    _HAS_RNNOISE = True
except Exception:
    _HAS_RNNOISE = False
    import noisereduce as nr

StrengthT = Literal["light", "medium", "strong"]

class RNNoiseEnhancer:
    """
    Denoise using RNNoise if available; otherwise spectral gating fallback.
    Works per-channel; keeps original sampling rate.
    """
    def __init__(self, strength: StrengthT = "medium"):
        self.strength = strength

    def enhance_waveform(self, waveform: torch.Tensor, sr: int) -> torch.Tensor:
        wf = waveform.detach().cpu().numpy()  # [C, T]
        out = []
        for c in range(wf.shape[0]):
            x = wf[c]
            if _HAS_RNNOISE:
                denoiser = RNNoise(sample_rate=48000)
                y = denoiser.denoise_chunk(x[np.newaxis, :])
            else:
                # Spectral gating fallback — tune aggressiveness via prop_decrease
                prop = {"light": 0.6, "medium": 0.8, "strong": 1.0}[self.strength]
                y = nr.reduce_noise(y=x, sr=sr, stationary=False, prop_decrease=prop)
            out.append(y)
        out_np = np.stack(out, axis=0)
        return torch.from_numpy(out_np).to(waveform.device)
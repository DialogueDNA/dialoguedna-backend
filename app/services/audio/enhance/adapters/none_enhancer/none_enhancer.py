from __future__ import annotations
import torch

class NoneEnhancer:
    """No-op enhancer; returns the input as-is."""
    def enhance_waveform(self, waveform: torch.Tensor, sr: int) -> torch.Tensor:
        return waveform
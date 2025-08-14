from __future__ import annotations
import torch

class CMGANEnhancer:
    """
    Placeholder for CMGAN speech enhancement.
    """
    def __init__(self, model_name: str = "cmgan"):
        self.model_name = model_name

    def enhance_waveform(self, waveform: torch.Tensor, sr: int) -> torch.Tensor:
        raise NotImplementedError("CMGAN enhancer not wired. Install & implement before use.")

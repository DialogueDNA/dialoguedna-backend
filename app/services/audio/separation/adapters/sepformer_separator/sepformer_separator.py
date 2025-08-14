from __future__ import annotations

import os
from typing import List, Optional
import torch
from speechbrain.inference.separation import SepformerSeparation

class SepformerSeparator:
    """
    Speech separation using SpeechBrain SepFormer.
    Splits a mixed waveform into N estimated sources.
    """
    def __init__(self, model_hub: str = "speechbrain/sepformer-whamr", device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.sep = SepformerSeparation.from_hparams(
            source=model_hub,
            savedir=os.path.join(os.path.expanduser("~"), ".cache", "speechbrain", "sepformer"),
            run_opts={"device": self.device},
        )

    def separate_waveform(self, waveform: torch.Tensor, sr: int) -> List[torch.Tensor]:
        """
        waveform: [C, T] torch tensor
        returns list of tensors [T] (mono streams)
        """
        # Merge channels to mono for separation
        if waveform.dim() == 2 and waveform.shape[0] > 1:
            mono = waveform.mean(dim=0, keepdim=True)
        else:
            mono = waveform
        est_sources = self.sep.separate_batch(mono.unsqueeze(0))  # [1, nsrc, T]
        out = [est_sources[0, i, :].detach().to(waveform.device) for i in range(est_sources.shape[1])]
        return out

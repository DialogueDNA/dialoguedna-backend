from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import torch

@dataclass
class AudioEnhancerInput:
    """
    Input for the audio enhancer.
    Contains the waveform and its sampling rate.
    """
    waveform: torch.Tensor
    sample_rate: int

class AudioEnhancerOutput:
    """
    Output for the audio enhancer.
    Contains the enhanced waveform.
    """
    enhanced_waveform: torch.Tensor

class AudioEnhancer(Protocol):
    def enhance(self, audio: AudioEnhancerInput) -> AudioEnhancerOutput: ...

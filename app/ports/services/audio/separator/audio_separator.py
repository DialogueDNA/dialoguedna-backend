from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List
import torch

@dataclass
class AudioSeparatorInput:
    """
    Input for the audio separator.
    Contains the waveform and its sampling rate.
    """
    waveform: torch.Tensor
    sample_rate: int

@dataclass
class AudioSeparatorOutput:
    """
    Output for the audio separator.
    Contains a list of separated waveforms, all aligned to the same sampling rate.
    """
    separated_waveforms: List[torch.Tensor]

class AudioSeparator(Protocol):
    """
    Separates a mixed-speaker waveform into N source streams.
    Returns a list of waveforms, all aligned to the same sampling rate.
    """
    def separate(self, audio: AudioSeparatorInput) -> AudioSeparatorOutput: ...

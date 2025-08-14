from dataclasses import dataclass
from typing import Optional, Union

import torch

from app.ports.services import SpeakerType

AudioPath = str
Waveform = torch.Tensor
AudioType = Union[AudioPath, Waveform]

@dataclass
class AudioSegment:
    speaker: Optional[SpeakerType]
    audio: AudioType
    start_time: Optional[float]
    end_time: Optional[float]
    sample_rate: Optional[int]
    language: Optional[str]
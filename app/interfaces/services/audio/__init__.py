from dataclasses import dataclass
from typing import Optional, Union

import torch

from app.interfaces.services import SpeakerType

AudioPath = str # Type alias for audio file paths, e.g., "path/to/audio.wav" or "http://example.com/audio.mp3" or similar
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
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List

from app.interfaces.services.audio import AudioSegment, AudioType

AudioSeparatorInput = AudioSegment

@dataclass
class AudioSeparatorOutput:
    separated_waveforms: List[AudioType]

class AudioSeparator(Protocol):
    def separate(self, audio: AudioSeparatorInput) -> AudioSeparatorOutput: ...

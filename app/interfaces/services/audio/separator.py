from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List

from app.interfaces.services.audio import AudioSegment, AudioType

AudioSeparatorInput = AudioSegment

@dataclass
class AudioSeparatorOutput:
    """
    Output for the audio separator.
    Contains a list of separated waveforms, all aligned to the same sampling rate.
    """
    separated_waveforms: List[AudioType]

class AudioSeparator(Protocol):
    def separate(self, audio: AudioSeparatorInput) -> AudioSeparatorOutput: ...

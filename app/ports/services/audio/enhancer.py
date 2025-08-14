from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.ports.services.audio import AudioSegment, AudioType

AudioEnhancerInput = AudioSegment

@dataclass
class AudioEnhancerOutput:
    """
    Output for the audio enhancer.
    Contains the enhanced waveform.
    """
    enhanced_audio: AudioType

class AudioEnhancer(Protocol):
    def enhance(self, audio: AudioEnhancerInput) -> AudioEnhancerOutput: ...

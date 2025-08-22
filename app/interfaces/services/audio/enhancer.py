from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.interfaces.services.audio import AudioSegment, AudioType

AudioEnhancerInput = AudioSegment

@dataclass
class AudioEnhancerOutput:
    enhanced_audio: AudioType

class AudioEnhancer(Protocol):
    def enhance(self, audio: AudioEnhancerInput) -> AudioEnhancerOutput: ...

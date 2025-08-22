from dataclasses import dataclass
from typing import Protocol

from app.interfaces.services.emotions.audio import EmotionAnalyzerByAudioOutput
from app.interfaces.services.emotions import EmotionAnalyzerOutput
from app.interfaces.services.emotions.text import EmotionAnalyzerByTextOutput

@dataclass
class EmotionAnalyzerMixerInput:
    text_results:  EmotionAnalyzerByTextOutput
    audio_results: EmotionAnalyzerByAudioOutput

EmotionAnalyzerMixerOutput = EmotionAnalyzerOutput

class EmotionMixedAnalyzer(Protocol):
    def fuse(self, mix_results: EmotionAnalyzerMixerInput) -> EmotionAnalyzerMixerOutput: ...
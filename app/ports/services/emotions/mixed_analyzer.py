from dataclasses import dataclass
from typing import Protocol

from app.ports.services.emotions.audio_analyzer import EmotionAnalyzerByAudioOutput
from app.ports.services.emotions import EmotionAnalyzerOutput
from app.ports.services.emotions.text_emotion_analyzer import EmotionAnalyzerByTextOutput

@dataclass
class EmotionAnalyzerMixerInput:
    """
    Input for the mixed emotion analyzer.
    Contains text results and audio results to be fused.
    """
    text_results: EmotionAnalyzerByTextOutput
    audio_results: EmotionAnalyzerByAudioOutput

EmotionAnalyzerMixerOutput = EmotionAnalyzerOutput

class MixedEmotionAnalyzer(Protocol):
    def fuse(self, mix_results: EmotionAnalyzerMixerInput) -> EmotionAnalyzerMixerOutput: ...
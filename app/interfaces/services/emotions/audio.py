from typing import Protocol

from app.interfaces.services.audio import AudioSegment
from app.interfaces.services.emotions import EmotionAnalyzerOutput

EmotionAnalyzerByAudioInput = AudioSegment
EmotionAnalyzerByAudioOutput = EmotionAnalyzerOutput

class EmotionAudioAnalyzer(Protocol):
    def analyze(self, segment: EmotionAnalyzerByAudioInput) -> EmotionAnalyzerByAudioOutput: ...
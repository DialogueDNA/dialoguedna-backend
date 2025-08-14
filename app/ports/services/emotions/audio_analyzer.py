from typing import Protocol

from app.ports.services.audio import AudioSegment
from app.ports.services.emotions import EmotionAnalyzerOutput

EmotionAnalyzerByAudioInput = AudioSegment
EmotionAnalyzerByAudioOutput = EmotionAnalyzerOutput

class AudioEmotionAnalyzer(Protocol):
    def analyze(self, segment: EmotionAnalyzerByAudioInput) -> EmotionAnalyzerByAudioOutput: ...
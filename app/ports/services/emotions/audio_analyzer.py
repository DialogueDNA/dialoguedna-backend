from typing import Protocol

from app.ports.services.audio.separator import AudioSeparator
from app.ports.services.emotions import EmotionAnalyzerOutput

EmotionAnalyzerByAudioInput = AudioSeparator
EmotionAnalyzerByAudioOutput = EmotionAnalyzerOutput

class AudioEmotionAnalyzer(Protocol):
    def analyze(self, segment: EmotionAnalyzerByAudioInput) -> EmotionAnalyzerByAudioOutput: ...
from typing import Protocol

from app.interfaces.services.emotions import EmotionAnalyzerOutput
from app.interfaces.services.transcription import TranscriptionSegmentOutput

EmotionAnalyzerByTextInput = TranscriptionSegmentOutput
EmotionAnalyzerByTextOutput = EmotionAnalyzerOutput

class EmotionTextAnalyzer(Protocol):
    def analyze(self, segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput: ...
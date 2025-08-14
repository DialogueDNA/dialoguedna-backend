from typing import Protocol

from app.ports.services.emotions import EmotionAnalyzerOutput
from app.ports.services.transcription import TranscriptionSegmentOutput

EmotionAnalyzerByTextInput = TranscriptionSegmentOutput
EmotionAnalyzerByTextOutput = EmotionAnalyzerOutput

class TextEmotionAnalyzer(Protocol):
    def analyze(self, segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput: ...
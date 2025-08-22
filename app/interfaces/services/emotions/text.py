from typing import Protocol

from app.interfaces.services.emotions import EmotionAnalyzerOutput
from app.interfaces.services.text import TextSegment

EmotionAnalyzerByTextInput =    TextSegment
EmotionAnalyzerByTextOutput =   EmotionAnalyzerOutput

class EmotionTextAnalyzer(Protocol):
    def analyze(self, segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput: ...
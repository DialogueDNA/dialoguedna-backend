from typing import Callable, Dict

from app.core.config.services.emotions import TextEmotionAnalysisConfig
from app.ports.services.emotions.text_analyzer import TextEmotionAnalyzer

TextEmotionAnalyzerPlugin = Callable[[TextEmotionAnalysisConfig], TextEmotionAnalyzer]
TEXT_EMOTION_ANALYZER_PLUGINS: Dict[str, TextEmotionAnalyzerPlugin] = {}

def register_text(name: str):
    def deco(fn: TextEmotionAnalyzerPlugin):
        TEXT_EMOTION_ANALYZER_PLUGINS[name] = fn
        return fn
    return deco

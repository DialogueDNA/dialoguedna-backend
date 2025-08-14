from typing import Callable, Dict

from app.core.config.services.emotions import MixedEmotionAnalysisConfig
from app.ports.services.emotions.mixed_analyzer import MixedEmotionAnalyzer

MixedEmotionAnalyzerPlugin = Callable[[MixedEmotionAnalysisConfig], MixedEmotionAnalyzer]
MIXED_EMOTION_ANALYZER_PLUGINS: Dict[str, MixedEmotionAnalyzerPlugin] = {}

def register_fusion(name: str):
    def deco(fn: MixedEmotionAnalyzerPlugin):
        MIXED_EMOTION_ANALYZER_PLUGINS[name] = fn
        return fn
    return deco
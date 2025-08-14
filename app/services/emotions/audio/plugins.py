from typing import Callable, Dict

from app.core.config.services.emotions import AudioEmotionAnalysisConfig
from app.ports.services.emotions.audio_analyzer import AudioEmotionAnalyzer

AudioEmotionAnalyzerPlugin = Callable[[AudioEmotionAnalysisConfig], AudioEmotionAnalyzer]
AUDIO_EMOTION_ANALYZER_PLUGINS: Dict[str, AudioEmotionAnalyzerPlugin] = {}

def register_audio(name: str):
    def deco(fn: AudioEmotionAnalyzerPlugin):
        AUDIO_EMOTION_ANALYZER_PLUGINS[name] = fn
        return fn
    return deco
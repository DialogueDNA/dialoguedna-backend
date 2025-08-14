from typing import Callable, Dict

from app.ports.services.emotions.audio_analyzer import AudioSegment, EmotionAnalyzerByAudioOutput

AUDIO_EMOTION_ANALYZER_PLUGIN = Callable[[AudioSegment], EmotionAnalyzerByAudioOutput]
AUDIO_EMOTION_ANALYZER_PLUGINS: Dict[str, AUDIO_EMOTION_ANALYZER_PLUGIN] = {}

def register_audio(name: str):
    def deco(fn: AUDIO_EMOTION_ANALYZER_PLUGIN):
        AUDIO_EMOTION_ANALYZER_PLUGINS[name] = fn
        return fn
    return deco
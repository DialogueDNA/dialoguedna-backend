from app.core.config.services.emotions import EmotionAudioAnalysisConfig
from app.interfaces.services.emotions.audio import EmotionAudioAnalyzer
from app.services.emotions.audio.providers.hugging_face.superb_audio_emotion_analyzer import SuperbAudioEmotionAnalyzer
from app.services.emotions.audio.registry import register_emotion_audio_analyzer


@register_emotion_audio_analyzer("hf-audio")
def build_superb_audio_emotion_analyzer(cfg: EmotionAudioAnalysisConfig) -> EmotionAudioAnalyzer:
    return SuperbAudioEmotionAnalyzer(cfg.superb)
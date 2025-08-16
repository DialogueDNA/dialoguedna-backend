from app.core.config.services.emotions import EmotionMixedAnalysisConfig
from app.interfaces.services.emotions.mixed import EmotionMixedAnalyzer
from app.services.emotions.mixed.adapters.adaptive.mixer import AdaptiveEmotionMixedMixer
from app.services.emotions.mixed.registry import register_emotion_mixed_analyzer


@register_emotion_mixed_analyzer("adaptive")
def build_adaptive_fusion(cfg: EmotionMixedAnalysisConfig) -> EmotionMixedAnalyzer:
    return AdaptiveEmotionMixedMixer(cfg.adaptive)
from app.core.config.services.emotions import EmotionMixedAnalysisConfig
from app.interfaces.services.emotions.mixed import EmotionMixedAnalyzer
from app.services.emotions.mixed.adapters.weights.model import MixEmotionMixedByWeights
from app.services.emotions.mixed.registry import register_emotion_mixed_analyzer


@register_emotion_mixed_analyzer("weights")
def build_emotion_mixed_analyzer(cfg: EmotionMixedAnalysisConfig) -> EmotionMixedAnalyzer:
    return MixEmotionMixedByWeights(cfg.weights)

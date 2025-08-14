from app.core.config.services.emotions import MixedEmotionAnalysisConfig
from app.services.emotions.mixed.adapters.weights.model import MixEmotionByWeights
from app.services.emotions.mixed.plugins import register_fusion


@register_fusion("weights")
def build_fusion_emotioner(cfg: MixedEmotionAnalysisConfig) -> MixEmotionByWeights:
    return MixEmotionByWeights(cfg.weights)

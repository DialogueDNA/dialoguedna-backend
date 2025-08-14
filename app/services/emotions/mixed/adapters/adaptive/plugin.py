from app.core.config.services.emotions import MixedEmotionAnalysisConfig
from app.services.emotions.mixed.adapters.adaptive.model import AdaptiveEmotionMixer
from app.services.emotions.mixed.adapters.weights.model import MixEmotionByWeights
from app.services.emotions.mixed.plugins import register_fusion


@register_fusion("adaptive")
def build_adaptive_fusion(cfg: MixedEmotionAnalysisConfig) -> MixEmotionByWeights:
    return AdaptiveEmotionMixer(cfg.adaptive)
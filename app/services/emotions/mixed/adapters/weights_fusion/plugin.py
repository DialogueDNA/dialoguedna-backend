from app.services.emotions.mixed.adapters.weights_fusion.weights_fusion import EmotionFusionByWeights
from app.services.emotions.mixed.plugins import register_fusion


@register_fusion("weights")
def build_fusion_emotioner(audio_weight: float = 0.6, text_weight: float = 0.4, time_decimals: int = 3, renorm: bool = True) -> EmotionFusionByWeights:
    return EmotionFusionByWeights(audio_weight=audio_weight, text_weight=text_weight, time_decimals=time_decimals, renorm=renorm)

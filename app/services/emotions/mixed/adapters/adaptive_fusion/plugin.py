from app.services.emotions.mixed.adapters.adaptive_fusion.adaptive_fusion import EmotionFusionByAdaptive
from app.services.emotions.mixed.plugins import register_fusion


@register_fusion("adaptive")
def build_adaptive_fusion(
    base_audio_w: float = 0.6,
    base_text_w: float = 0.4,
    time_decimals: int = 3,
    renorm: bool = True,
) -> EmotionFusionByAdaptive:
    return EmotionFusionByAdaptive(
        base_audio_w=base_audio_w,
        base_text_w=base_text_w,
        time_decimals=time_decimals,
        renorm=renorm,
    )
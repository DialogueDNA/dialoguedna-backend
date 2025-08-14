from app.services.audio.enhance.adapters.rnnoise_enhancer.rnnoise_enhancer import StrengthT, RNNoiseEnhancer
from app.services.emotions.plugins import register_enhancer

@register_enhancer("rnnoise")
def build_rnnoise_enhancer(strength: StrengthT = "medium") -> RNNoiseEnhancer:
    return RNNoiseEnhancer(strength=strength)

from app.core.config.services.audio import AudioEnhancerConfig
from app.services.audio.enhance.adapters.rnnoise_enhancer.rnnoise_enhancer import RNNoiseEnhancer
from app.services.audio.enhance.plugins import register_enhancer


@register_enhancer("rnnoise")
def build_rnnoise_enhancer(audio_enhancer_cfg: AudioEnhancerConfig) -> RNNoiseEnhancer:
    return RNNoiseEnhancer(audio_enhancer_cfg.rnnoise)

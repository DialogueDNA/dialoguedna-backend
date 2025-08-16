from app.core.config.services.audio import AudioEnhancerConfig
from app.services.audio.enhance.providers.rnnoise.rnnoise_enhancer import RNNoiseEnhancer
from app.services.audio.enhance.registry import register_audio_enhancer


@register_audio_enhancer("rnnoise")
def build_rnnoise_enhancer(audio_enhancer_cfg: AudioEnhancerConfig) -> RNNoiseEnhancer:
    return RNNoiseEnhancer(audio_enhancer_cfg.rnnoise)

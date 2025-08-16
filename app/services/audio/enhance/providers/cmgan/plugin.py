from app.core.config.services.audio import AudioEnhancerConfig
from app.interfaces.services.audio.enhancer import AudioEnhancer
from app.services.audio.enhance.providers.cmgan.cmgan_enhancer import CMGANEnhancer
from app.services.audio.enhance.registry import register_audio_enhancer


@register_audio_enhancer("cmgan")
def build_cmgan_enhancer(cfg: AudioEnhancerConfig) -> AudioEnhancer:
    return CMGANEnhancer(cfg.cmgan)
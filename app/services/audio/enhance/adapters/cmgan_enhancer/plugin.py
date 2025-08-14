from app.core.config.services.audio import AudioEnhancerConfig
from app.ports.services.audio.enhancer import AudioEnhancer
from app.services.audio.enhance.adapters.cmgan_enhancer.cmgan_enhancer import CMGANEnhancer
from app.services.audio.enhance.plugins import register_enhancer


@register_enhancer("cmgan")
def build_cmgan_enhancer(cfg: AudioEnhancerConfig) -> AudioEnhancer:
    return CMGANEnhancer(cfg.cmgan)
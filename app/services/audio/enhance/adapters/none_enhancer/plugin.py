from app.core.config.services.audio import AudioEnhancerConfig
from app.ports.services.audio.enhancer import AudioEnhancer
from app.services.audio.enhance.adapters.none_enhancer.none_enhancer import NoneEnhancer
from app.services.audio.enhance.plugins import register_enhancer


@register_enhancer("none")
def build_none_enhancer(cfg: AudioEnhancerConfig) -> AudioEnhancer:
    return NoneEnhancer()

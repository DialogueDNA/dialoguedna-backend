from app.core.config.services.audio import AudioEnhancerConfig
from app.interfaces.services.audio.enhancer import AudioEnhancer
from app.services.audio.enhance.providers.none.none_enhancer import NoneEnhancer
from app.services.audio.enhance.registry import register_audio_enhancer


@register_audio_enhancer("none")
def build_none_enhancer(cfg: AudioEnhancerConfig) -> AudioEnhancer:
    return NoneEnhancer()

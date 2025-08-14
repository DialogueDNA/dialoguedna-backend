from app.core.config.services.audio import AudioEnhancerConfig
from app.ports.services.audio.enhancer import AudioEnhancer
from app.services.audio.enhance.adapters.demucs_enhancer.demucs_enhancer import DemucsEnhancer
from app.services.audio.enhance.plugins import register_enhancer


@register_enhancer("demucs")
def build_demucs_enhancer(cfg: AudioEnhancerConfig) -> AudioEnhancer:
    return DemucsEnhancer(cfg.demucs)
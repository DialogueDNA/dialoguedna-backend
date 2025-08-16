from app.core.config.services.audio import AudioEnhancerConfig
from app.interfaces.services.audio.enhancer import AudioEnhancer
from app.services.audio.enhance.providers.demucs.demucs_enhancer import DemucsEnhancer
from app.services.audio.enhance.registry import register_audio_enhancer


@register_audio_enhancer("demucs")
def build_demucs_enhancer(cfg: AudioEnhancerConfig) -> AudioEnhancer:
    return DemucsEnhancer(cfg.demucs)
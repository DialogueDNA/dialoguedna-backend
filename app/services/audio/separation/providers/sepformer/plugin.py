from app.core.config.services.audio import AudioSeparatorConfig
from app.interfaces.services.audio.separator import AudioSeparator
from app.services.audio.separation.providers.sepformer.sepformer_separator import SepformerSeparator
from app.services.audio.separation.registry import register_audio_separator


@register_audio_separator("sepformer")
def build_sepformer_separator(cfg: AudioSeparatorConfig) -> AudioSeparator:
    return SepformerSeparator(cfg.sepformer)
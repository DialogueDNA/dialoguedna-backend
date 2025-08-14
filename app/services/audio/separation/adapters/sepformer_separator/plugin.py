from app.core.config.services.audio import AudioSeparatorConfig
from app.ports.services.audio.separator import AudioSeparator
from app.services.audio.separation.adapters.sepformer_separator.sepformer_separator import SepformerSeparator
from app.services.audio.separation.plugins import register_separator


@register_separator("sepformer")
def build_sepformer_separator(cfg: AudioSeparatorConfig) -> AudioSeparator:
    return SepformerSeparator(cfg.sepformer)
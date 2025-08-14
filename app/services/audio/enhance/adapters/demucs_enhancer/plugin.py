from app.services.audio.enhance.adapters.demucs_enhancer.demucs_enhancer import DemucsEnhancer
from app.services.emotions.plugins import register_enhancer


@register_enhancer("demucs")
def build_demucs_enhancer(model_name: str = "htdemucs") -> DemucsEnhancer:
    return DemucsEnhancer(model_name=model_name)
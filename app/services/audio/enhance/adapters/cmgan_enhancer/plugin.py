from app.services.audio.enhance.adapters.cmgan_enhancer.cmgan_enhancer import CMGANEnhancer
from app.services.emotions.plugins import register_enhancer


@register_enhancer("cmgan")
def build_cmgan_enhancer(model_name: str = "cmgan") -> CMGANEnhancer:
    return CMGANEnhancer(model_name=model_name)
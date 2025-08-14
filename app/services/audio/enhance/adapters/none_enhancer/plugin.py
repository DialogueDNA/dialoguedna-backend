from app.services.audio.enhance.adapters.none_enhancer.none_enhancer import NoneEnhancer
from app.services.emotions.plugins import register_enhancer


@register_enhancer("none")
def build_none_enhancer() -> NoneEnhancer:
    return NoneEnhancer()

from typing import Callable, Dict

from app.core.config.services.audio import AudioEnhancerConfig
from app.ports.services.audio.enhancer import AudioEnhancer

AudioEnhancerPlugin = Callable[[AudioEnhancerConfig], AudioEnhancer]
ENHANCER_PLUGINS: Dict[str, AudioEnhancerPlugin] = {}

def register_enhancer(name: str):
    def deco(fn: AudioEnhancerPlugin):
        ENHANCER_PLUGINS[name] = fn
        return fn
    return deco
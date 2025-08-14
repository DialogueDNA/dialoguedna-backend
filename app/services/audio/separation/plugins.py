from typing import Callable, Dict

from app.core.config.services.audio import AudioSeparatorConfig
from app.ports.services.audio.separator import AudioSeparator

AudioSeparatorPlugin = Callable[[AudioSeparatorConfig], AudioSeparator]

SEPARATOR_PLUGINS: Dict[str, AudioSeparatorPlugin] = {}

def register_separator(name: str):
    def deco(fn: AudioSeparatorPlugin):
        SEPARATOR_PLUGINS[name] = fn
        return fn
    return deco

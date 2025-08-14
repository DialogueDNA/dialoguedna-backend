from typing import Callable, Any, Dict

AUDIO_PLUGINS: Dict[str, Callable[..., Any]] = {}

def register_audio(name: str):
    def deco(fn: Callable[..., Any]):
        AUDIO_PLUGINS[name] = fn
        return fn
    return deco
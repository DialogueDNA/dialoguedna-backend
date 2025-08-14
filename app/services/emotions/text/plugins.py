from typing import Callable, Dict, Any

TEXT_PLUGINS: Dict[str, Callable[..., Any]] = {}

def register_text(name: str):
    def deco(fn: Callable[..., Any]):
        TEXT_PLUGINS[name] = fn
        return fn
    return deco

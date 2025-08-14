from typing import Callable, Any, Dict

ENHANCER_PLUGINS: Dict[str, Callable[..., Any]] = {}

def register_enhancer(name: str):
    def deco(fn: Callable[..., Any]):
        ENHANCER_PLUGINS[name] = fn
        return fn
    return deco
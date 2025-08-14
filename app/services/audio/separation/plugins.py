from typing import Callable, Any, Dict

SEPARATOR_PLUGINS: Dict[str, Callable[..., Any]] = {}

def register_separator(name: str):
    def deco(fn: Callable[..., Any]):
        SEPARATOR_PLUGINS[name] = fn
        return fn
    return deco

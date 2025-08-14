from typing import Callable, Any, Dict

FUSION_PLUGINS: Dict[str, Callable[..., Any]] = {}

def register_fusion(name: str):
    def deco(fn: Callable[..., Any]):
        FUSION_PLUGINS[name] = fn
        return fn
    return deco
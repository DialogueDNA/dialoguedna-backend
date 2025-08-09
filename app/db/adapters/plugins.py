# app/db/adapters/plugins.py
from typing import Callable
from app.db.registry import TableGatewayFactory
from app.settings.config import AppConfig

# Type alias for a plugin function that takes an AppConfig and returns a TableGatewayFactory
Plugin = Callable[[AppConfig, object], TableGatewayFactory]

PLUGINS: dict[str, Plugin] = {}

def register_adapter(backend: str):
    def deco(fn: Plugin):
        PLUGINS[backend] = fn
        return fn
    return deco

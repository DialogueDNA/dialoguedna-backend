# app/db/adapters/plugins.py
from typing import Callable, Dict
from app.settings.config import DBConfig
from app.state.types import DBState
from app.ports.db.table_gateway import TableGateway

TableGatewayFactory = Callable[[str], TableGateway]
Plugin = Callable[[DBConfig, DBState], TableGatewayFactory]

PLUGINS: Dict[str, Plugin] = {}

def register_adapter(backend: str):
    def deco(fn: Plugin):
        PLUGINS[backend] = fn
        return fn
    return deco

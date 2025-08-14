# app/database/adapters/plugins.py
from typing import Callable, Dict
from app.core.config import DatabaseConfig
from app.state.app_states import DatabaseState
from app.ports.db.table_gateway import TableGateway

TableGatewayFactory = Callable[[str], TableGateway]
DBPlugin = Callable[[DatabaseConfig, DatabaseState], TableGatewayFactory]

PLUGINS: Dict[str, DBPlugin] = {}

def register_adapter(backend: str):
    def deco(fn: DBPlugin):
        PLUGINS[backend] = fn
        return fn
    return deco

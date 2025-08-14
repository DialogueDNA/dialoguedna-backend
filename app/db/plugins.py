from typing import Callable, Dict
from app.core.config import DatabaseConfig
from app.state.app_states import DatabaseState
from app.ports.db.table_gateway import TableGateway

TableGatewayFactory = Callable[[str], TableGateway]
DatabasePlugin = Callable[[DatabaseState, DatabaseConfig], TableGatewayFactory]

DATABASE_PLUGINS: Dict[str, DatabasePlugin] = {}

def register_adapter(backend: str):
    def deco(fn: DatabasePlugin):
        DATABASE_PLUGINS[backend] = fn
        return fn
    return deco

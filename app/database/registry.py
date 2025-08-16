from typing import Callable, Dict

from app.core.config.database.database import DatabaseConfig
from app.interfaces.db.table_gateway import TableGateway

TableGatewayFactory = Callable[[str], TableGateway]
DATABASE_PLUGIN = Callable[[DatabaseConfig], TableGatewayFactory]

DATABASE_PLUGINS: Dict[str, DATABASE_PLUGIN] = {}

def register_database(backend: str):
    def deco(fn: DATABASE_PLUGIN):
        DATABASE_PLUGINS[backend] = fn
        return fn
    return deco
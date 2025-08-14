from app.database.plugins import register_adapter, TableGatewayFactory
from app.core.config import DatabaseConfig
from app.state.app_states import DatabaseState
from app.database.adapters.supabase.supabase_table import SupabaseTable
from supabase import create_client

@register_adapter("supabase")
def build_supabase_factory(database: DatabaseState, database_cfg: DatabaseConfig) -> TableGatewayFactory:
    if not hasattr(database, "supabase_client"):
        database.supabase_client = create_client(database_cfg.supabase.url, database_cfg.supabase.key)
    return lambda table_name: SupabaseTable(database.supabase_client, table_name)

from app.db.plugins import register_adapter, TableGatewayFactory
from app.core.config import DatabaseConfig
from app.state.app_states import DatabaseState
from app.db.adapters.supabase.supabase_table import SupabaseTable
from supabase import create_client

@register_adapter("supabase")
def build_supabase_factory(cfg: DatabaseConfig, db: DatabaseState) -> TableGatewayFactory:
    if not hasattr(db, "supabase_client"):
        db.supabase_client = create_client(cfg.supabase_url, cfg.supabase_key)
    return lambda table_name: SupabaseTable(db.supabase_client, table_name)

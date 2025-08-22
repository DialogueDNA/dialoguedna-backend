from app.core.config.database.database import DatabaseConfig
from app.database.gateways.providers.supabase.supabase_gateway import SupabaseTable
from app.database.registry import TableGatewayFactory, register_database


@register_database("supabase")
def build_supabase_factory(cfg: DatabaseConfig) -> TableGatewayFactory:
    return lambda table_name: SupabaseTable.from_config(cfg.supabase, table_name)
# app/db/adapters/supabase/plugin.py
from supabase import create_client
from app.db.adapters.plugins import register_adapter
from app.db.adapters.supabase.supabase_table import SupabaseTable
from app.settings.config import AppConfig
from app.db.registry import TableGatewayFactory

BACKEND = "supabase"

@register_adapter(BACKEND)
def build_supabase_factory(config: AppConfig, app_state) -> TableGatewayFactory:
    # Initialize Supabase client if not already done
    if not getattr(app_state, BACKEND, None):
        app_state.supabase = create_client(config.supabase_url, config.supabase_key)
    return lambda table_name: SupabaseTable(app_state.supabase, table_name)

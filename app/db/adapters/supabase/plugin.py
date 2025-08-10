# app/db/adapters/supabase/plugin.py
from typing import Callable

from app.db.adapters.plugins import register_adapter
from app.settings.config import DBConfig
from app.state.types import DBState
from app.ports.db.table_gateway import TableGateway
from app.db.adapters.supabase.supabase_table import SupabaseTable
from supabase import create_client

@register_adapter("supabase")
def build_supabase_factory(cfg: DBConfig, db: DBState) -> Callable[[str], TableGateway]:
    if not hasattr(db, "supabase_client"):
        db.supabase_client = create_client(cfg.supabase_url, cfg.supabase_key)
    return lambda table_name: SupabaseTable(db.supabase_client, table_name)

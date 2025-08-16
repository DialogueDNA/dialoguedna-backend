from supabase import create_client

from app.core.config.providers.supabase.supabase import SupabaseConfig
from app.interfaces.db.table_gateway import TableGateway


class SupabaseTable(TableGateway):
    def __init__(self, client, table: str):
        self._t = client.table(table)

    @classmethod
    def from_config(cls, cfg: SupabaseConfig, table: str) -> "SupabaseTable":
        if hasattr(cfg, "url") and hasattr(cfg, "key"):
            client = create_client(cfg.url, cfg.key)
        else:
            raise ValueError("SupabaseConfig must have 'url' and 'key' attributes")
        return cls(client, table)

    def insert(self, data): return self._t.insert(data).execute()
    def update(self, f, u):
        q = self._t.update(u)
        for k, v in f.items(): q = q.eq(k, v)
        return q.execute()
    def select_one(self, f):
        q = self._t.select("*")
        for k, v in f.items(): q = q.eq(k, v)
        return q.single().execute()
    def select_many(self, f):
        q = self._t.select("*")
        for k, v in f.items(): q = q.eq(k, v)
        return q.execute()
    def delete(self, f):
        q = self._t.delete()
        for k, v in f.items(): q = q.eq(k, v)
        return q.execute()
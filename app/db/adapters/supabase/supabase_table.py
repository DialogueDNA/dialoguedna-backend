# app/db/adapters/supabase_table.py
from app.db.ports.table_gateway import TableGateway

class SupabaseTable(TableGateway):
    def __init__(self, client, table: str):
        self._t = client.table(table)

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

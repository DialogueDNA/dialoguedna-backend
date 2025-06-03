from app.core.config import supabase

class SupabaseDB:
    def __init__(self, table_name: str):
        self.table = supabase.table(table_name)

    def insert(self, data: dict):
        return self.table.insert(data).execute()

    def update(self, filters: dict, updates: dict):
        query = self.table.update(updates)
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute()

    def select_one(self, filters: dict):
        query = self.table.select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.single().execute()

    def select_many(self, filters: dict):
        query = self.table.select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute()

    def delete(self, filters: dict):
        query = self.table.delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute()

    def delete_in(self, key: str, values: list[str]):
        return self.table.delete().in_(key, values).execute()
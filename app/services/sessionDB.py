from typing import Optional

from app.core.config import supabase

class SessionDB:
    def __init__(self, table_name="sessions"):
        self.table = supabase.table(table_name)

    def create_session(self, data: dict) -> str:
        response = self.table.insert(data).execute()
        if not response.data or "id" not in response.data[0]:
            raise RuntimeError("Failed to create session record")
        return response.data[0]["id"]

    def update_session(self, session_id: str, updates: dict):
        self.table.update(updates).eq("id", session_id).execute()

    def set_status(self, session_id: str, field: str, value: str, error: Optional[str] = None):
        self.table.update({
            field: value,
            "processing_error": error
        }).eq("id", session_id).execute()

    def get_session(self, session_id: str) -> dict:
        response = self.table.select("*").eq("id", session_id).single().execute()
        return response.data

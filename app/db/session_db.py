from typing import Optional, Any

import app.db.superbase.supabase_db as db_service
import app.settings.constants.db.supabase_constants as db_constants


class SessionDB:
    def __init__(self):
        self.db = db_service.SupabaseDB(db_constants.SESSIONS_TABLE_NAME)

    def create_session(self, data: dict) -> str:
        response = self.db.insert(data)
        if not response.data or db_constants.SESSIONS_COLUMN_UNIQUE_ID not in response.data[0]:
            raise RuntimeError("Failed to create session record")
        return response.data[0][db_constants.SESSIONS_COLUMN_UNIQUE_ID]

    def update_session(self, session_id: str, updates: dict):
        self.db.update({db_constants.SESSIONS_COLUMN_UNIQUE_ID: session_id}, updates)

    def set_status(self, session_id: str, field: str, value: Any, error: Optional[str] = None):
        updates = {field: value, "processing_error": error}
        self.db.update({db_constants.SESSIONS_COLUMN_UNIQUE_ID: session_id}, updates)

    def get_session(self, session_id: str) -> dict:
        response = self.db.select_one({db_constants.SESSIONS_COLUMN_UNIQUE_ID: session_id})
        return response.data

    def get_all_sessions_for_user(self, user_id: str) -> list:
        response = self.db.select_many({db_constants.SESSIONS_COLUMN_USER_ID: user_id})
        return response.data

    def delete_session(self, session_id: str):
        try:
            response = self.db.delete({db_constants.SESSIONS_COLUMN_UNIQUE_ID: session_id})
            if response.data is None:
                raise RuntimeError(f"Failed to delete session {session_id}: no response data")
        except Exception as e:
            raise RuntimeError(f"Failed to delete session {session_id}: {str(e)}")

    def delete_sessions(self, session_ids: list[str]):
        if not session_ids:
            return
        try:
            response = self.db.delete_in(db_constants.SESSIONS_COLUMN_UNIQUE_ID, session_ids)
            if response.data is None:
                raise RuntimeError("Failed to delete sessions: no response data")
        except Exception as e:
            raise RuntimeError(f"Failed to delete sessions: {str(e)}")
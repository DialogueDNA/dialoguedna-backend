from typing import Any
from app.interfaces.db.domains.sessions_repo import SessionsRepo
from app.interfaces.db.table_gateway import TableGateway
from app.models.session import SessionDB

class SessionsRepoImpl(SessionsRepo):
    def __init__(self, table_gateway: TableGateway[SessionDB]):
        self.t: TableGateway[SessionDB] = table_gateway

    @staticmethod
    def _to_dict(session: SessionDB | dict[str, Any]) -> dict[str, Any]:
        if isinstance(session, SessionDB):
            return session.model_dump(exclude_none=True)
        return session

    def create(self, session: SessionDB | dict[str, Any]) -> SessionDB:
        return self.t.insert(self._to_dict(session))

    def get_for_user(self, session_id: str, user_id: str) -> SessionDB | None:
        return self.t.select_one({"id": session_id, "user_id": user_id})

    def list_for_user(self, user_id: str) -> list[SessionDB]:
        return self.t.select_many({"user_id": user_id})

    def update(self, session_id: str, updates: dict[str, Any]) -> SessionDB:
        return self.t.update({"id": session_id}, updates)

    def delete(self, session_id: str) -> bool:
        return self.t.delete({"id": session_id})

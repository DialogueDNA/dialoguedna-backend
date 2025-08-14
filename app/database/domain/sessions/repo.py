from app.ports.db.domains.sessions_repo import SessionsRepo
from app.database.registry.repositories import register_repo

@register_repo(domain="sessions", table="sessions")
class SessionsRepoImpl(SessionsRepo):
    def __init__(self, table_gateway):
        self.t = table_gateway
    def create(self, session): return self.t.insert(session)
    def get(self, session_id): return self.t.select_one({"id": session_id})
    def list_for_user(self, user_id): return self.t.select_many({"user_id": user_id})
    def update(self, session_id, updates): return self.t.update({"id": session_id}, updates)
    def delete(self, session_id): return self.t.delete({"id": session_id})

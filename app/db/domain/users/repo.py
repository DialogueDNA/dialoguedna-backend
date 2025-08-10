# app/db/domain/users/repo.py
from app.ports import UsersRepo
from app.db.registry.repositories import register_repo

@register_repo("users", table="users")
class UsersRepoImpl(UsersRepo):
    def __init__(self, table_gateway):
        self.t = table_gateway
    def create(self, user): return self.t.insert(user)
    def get(self, user_id): return self.t.select_one({"id": user_id})
    def list_all(self): return self.t.select_many({})
    def update(self, user_id, updates): return self.t.update({"id": user_id}, updates)
    def delete(self, user_id): return self.t.delete({"id": user_id})

from typing import Callable

from app.database.repos.registry import register_repo
from app.database.repos.users.repo import UsersRepoImpl


@register_repo("users", table="users")
def build_users_repo(table_gateway: Callable):
    return UsersRepoImpl(table_gateway)

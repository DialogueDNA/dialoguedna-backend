from typing import Callable

from app.database.repos.registry import register_repo
from app.database.repos.sessions.repo import SessionsRepoImpl


@register_repo(domain="sessions", table="sessions")
def build_sessions_repo(table_gateway: Callable):
    return SessionsRepoImpl(table_gateway)

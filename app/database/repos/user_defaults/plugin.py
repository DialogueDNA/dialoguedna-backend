from typing import Callable

from app.database.repos.registry import register_repo
from app.database.repos.user_defaults.repo import UserDefaultsRepoImpl


@register_repo(domain="user_defaults", table="user_defaults")
def build_user_defaults_repo(table_gateway: Callable):
    return UserDefaultsRepoImpl(table_gateway)

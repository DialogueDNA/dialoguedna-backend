# app/database/registry/repositories.py
from dataclasses import dataclass
from typing import Callable, Dict

@dataclass(frozen=True)
class RepoMeta:
    ctor: Callable  # ctor(table_gateway) -> RepoInstance
    table: str      # logical table name (can differ per backend if needed)

class RepoRegistry:
    def __init__(self) -> None:
        self._by_domain: Dict[str, RepoMeta] = {}

    def register(self, domain: str, ctor: Callable, table: str) -> None:
        self._by_domain[domain] = RepoMeta(ctor=ctor, table=table)

    def get(self, domain: str) -> RepoMeta:
        if domain not in self._by_domain:
            raise KeyError(f"Repo not registered for domain: {domain}")
        return self._by_domain[domain]

repo_registry = RepoRegistry()

# helper decorator for convenient registration
def register_repo(domain: str, *, table: str):
    def deco(ctor: Callable):
        repo_registry.register(domain, ctor, table)
        return ctor
    return deco

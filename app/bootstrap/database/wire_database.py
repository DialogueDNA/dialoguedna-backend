from __future__ import annotations

from app.core.config import DatabaseConfig
from app.state.app_states import DatabaseState
from app.database.registry import GatewayRegistry, repo_registry
from app.database.plugins import DATABASE_PLUGINS as DB_PLUGINS

def wire_database(db: DatabaseState, db_config: DatabaseConfig) -> None:
    gw = GatewayRegistry()

    for backend in db_config.backends_in_use:
        build_factory = DB_PLUGINS.get(backend)
        if not build_factory:
            raise ValueError(f"No DB adapter plugin registered for backend: {backend}")
        gw.register(backend, build_factory(db_config, db))

    db.gateway_registry = gw

    for domain, backend in db_config.domain_backends.items():
        meta = repo_registry.get(domain)
        factory = gw.for_backend(backend)
        repo_instance = meta.ctor(factory(meta.table))
        setattr(db, f"{domain}_repo", repo_instance)

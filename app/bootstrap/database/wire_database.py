from __future__ import annotations

from app.core.config.database.database import DatabaseConfig
from app.database.gateways.registry import GatewayRegistry
from app.database.registry import DATABASE_PLUGINS
from app.database.repos.registry import repo_registry
from app.state.app_states import DatabaseState


def wire_database(database_cfg: DatabaseConfig) -> DatabaseState:
    database = DatabaseState()
    gw = GatewayRegistry()

    name = (getattr(database_cfg, "main_database", "") or "").strip().lower()
    if not name:
        raise ValueError("DatabaseConfig.main_database is empty")

    for database_name in database_cfg.backends_in_use:
        build_factory = DATABASE_PLUGINS.get(database_name)
        if not build_factory:
            raise ValueError(f"No DB adapter plugin registered for database_name: {database_name}")
        gw.register(database_name, build_factory(database_cfg))

    database.gateway_registry = gw

    for domain, database_name in database_cfg.domain_backends.items():
        meta = repo_registry.get(domain)
        factory = gw.for_backend(database_name)
        repo_instance = meta.ctor(factory(meta.table))
        setattr(database, f"{domain}_repo", repo_instance)

    return database

# app/bootstrap/wire_db.py
from __future__ import annotations

from app.settings.config import DBConfig
from app.state.types import DBState
from app.db.registry import GatewayRegistry, repo_registry
from app.db.adapters.plugins import PLUGINS as DB_PLUGINS  # backend -> (config, db_state) -> TableGatewayFactory

def wire_db(db: DBState, db_config: DBConfig) -> None:
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

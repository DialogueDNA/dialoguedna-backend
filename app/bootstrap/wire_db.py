# app/bootstrap/wire_db.py
from app.db.registry import GatewayRegistry, repo_registry
from app.db.adapters.plugins import PLUGINS
from app.settings.config import AppConfig

def wire_db(app, config: AppConfig):
    gw = GatewayRegistry()

    # Register database gateways for each backend
    for backend in config.backends_in_use:
        try:
            build_factory = PLUGINS[backend]
        except KeyError:
            raise ValueError(f"No adapter plugin registered for backend: {backend}")
        gw.register(backend, build_factory(config, app.state))

    app.state.gateway_registry = gw

    # Register repositories for each domain
    for domain, backend in config.domain_backends.items():
        meta = repo_registry.get(domain)
        factory = gw.for_backend(backend)
        repo_instance = meta.ctor(factory(meta.table))
        setattr(app.state, f"{domain}_repo", repo_instance)

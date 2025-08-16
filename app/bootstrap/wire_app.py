from app.bootstrap.database.wire_database import wire_database
from app.bootstrap.storage.wire_storage import wire_storage
from app.bootstrap.services.wire_services import wire_services
from app.common.plugin_discovery import discover_plugins
from app.core.config import AppConfig
from app.state.app_states import AppState


def wire_app(app_cfg: AppConfig) -> AppState:
    """
    Wire the application with all necessary services and configurations.
    """

    discover_plugins()
    database = wire_database(app_cfg.database)
    storage = wire_storage(app_cfg.storage)
    services = wire_services(app_cfg.services)

    return AppState(database=database, storage=storage, services=services)
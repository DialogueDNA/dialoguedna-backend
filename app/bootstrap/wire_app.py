from app.bootstrap.database.wire_database import wire_database
from app.bootstrap.storage.wire_storage import wire_storage
from app.bootstrap.services.wire_services import wire_services
from app.core.config import AppConfig
from app.state.app_states import AppState


def wire_app(app: AppState, app_cfg: AppConfig) -> None:
    """
    Wire the application with all necessary services and configurations.
    """

    wire_database(app.database, app_cfg.database)
    wire_storage(app.storage, app_cfg.storage)
    wire_services(app.services, app_cfg.services)
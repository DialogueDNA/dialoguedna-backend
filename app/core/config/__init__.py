from dataclasses import dataclass

from app.core.config.database.database import DatabaseConfig
from app.core.config.policy.policy import PolicyConfig
from app.core.config.services import ServicesConfig
from app.core.config.storage.storage import StorageConfig

@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig = DatabaseConfig()
    storage: StorageConfig = StorageConfig()
    services: ServicesConfig = ServicesConfig()
    policy: PolicyConfig = PolicyConfig()

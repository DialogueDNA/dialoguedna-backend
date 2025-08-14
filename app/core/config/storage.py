from dataclasses import dataclass
import app.core.environment as env
from app.core.config.providers.azure_blob import AzureBlobConfig


@dataclass(frozen=True)
class StorageConfig:
    main_storage: str = env.STORAGE_ADAPTER
    azure: AzureBlobConfig = AzureBlobConfig()

    # Local File System
    # local_root: str = env.LOCAL_STORAGE_ROOT
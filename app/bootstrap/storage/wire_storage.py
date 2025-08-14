from __future__ import annotations
from app.storage.plugins import STORAGE_PLUGINS
from app.state.app_states import StorageState
from app.core.config import StorageConfig

def wire_storage(storage: StorageState, storage_config: StorageConfig) -> None:
    builder = STORAGE_PLUGINS.get(storage_config.main_storage)
    if not builder:
        raise ValueError(f"No storage plugin registered for backend: {storage_config.main_storage}")
    storage.client = builder(storage_config, storage)
    if not storage.client:
        raise RuntimeError("Storage wiring failed: no BlobStorage client.")

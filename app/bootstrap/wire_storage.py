# app/bootstrap/wire_storage.py
from __future__ import annotations
from app.storage.adapters.plugins import STORAGE_PLUGINS
from app.state.types import StorageState
from app.settings.config import StorageConfig

def wire_storage(storage: StorageState, storage_config: StorageConfig) -> None:
    builder = STORAGE_PLUGINS.get(storage_config.backend)
    if not builder:
        raise ValueError(f"No storage plugin registered for backend: {storage_config.backend}")
    storage.client = builder(storage_config, storage)

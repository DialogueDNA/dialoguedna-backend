# app/storage/plugins.py
from __future__ import annotations
from typing import Callable, Dict
from app.settings.config import StorageConfig
from app.ports.storage.blob_storage import BlobStorage
from app.state.types import StorageState

# Plugin signature: (config, storage_state) -> BlobStorage
StoragePlugin = Callable[[StorageConfig, StorageState], BlobStorage]

STORAGE_PLUGINS: Dict[str, StoragePlugin] = {}

def register_storage(backend: str):
    def deco(fn: StoragePlugin):
        STORAGE_PLUGINS[backend] = fn
        return fn
    return deco

from __future__ import annotations
from app.storage.registry import build_storage, list_storages
from app.state.app_states import StorageState
from app.core.config import StorageConfig

def wire_storage(storage_cfg: StorageConfig) -> StorageState:
    storage = StorageState()
    name = (getattr(storage_cfg, "main_storage", "") or "").strip().lower()
    if not name:
        raise ValueError("StorageConfig.main_storage is empty")

    try:
        storage.client = build_storage(name, storage_cfg)
        if not storage.client:
            raise RuntimeError("Storage wiring failed: no BlobStorage client.")
    except KeyError:
        raise ValueError(
            f"No storage plugin registered for: '{name}'. "
            f"Available: {', '.join(list_storages())}"
        )
    return storage

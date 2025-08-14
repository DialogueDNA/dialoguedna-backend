from __future__ import annotations
from app.ports.storage.blob_storage import BlobStorage
from app.storage.adapters.local.local_fs import LocalFSAdapter
from app.storage.plugins import register_storage
from app.core.config import StorageConfig

@register_storage("local")
def build_local_storage(config: StorageConfig, app_state) -> BlobStorage:
    root = config.local_root or "./.storage"
    return LocalFSAdapter(root=root)

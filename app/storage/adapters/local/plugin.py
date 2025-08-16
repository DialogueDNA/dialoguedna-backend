from __future__ import annotations
from app.interfaces.storage.blob_storage import BlobStorage
from app.storage.adapters.local.local_fs import LocalFSAdapter
from app.storage.registry import register_storage
from app.core.config import StorageConfig

@register_storage("local")
def build_local_storage(cfg: StorageConfig) -> BlobStorage:
    root = cfg.local_root or "./.storage"
    return LocalFSAdapter(root=root)

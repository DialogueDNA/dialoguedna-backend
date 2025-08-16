from __future__ import annotations
from app.interfaces.storage.blob_storage import BlobStorage
from app.storage.providers.azure.azure_blob import AzureBlobStorage
from app.storage.registry import register_storage
from app.core.config import StorageConfig

@register_storage("azure_blob")
def build_azure_storage(cfg: StorageConfig) -> BlobStorage:
    return AzureBlobStorage.from_config(cfg)
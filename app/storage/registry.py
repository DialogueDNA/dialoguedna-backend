from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config import StorageConfig
from app.interfaces.storage.blob_storage import BlobStorage

# Typed registry for storages
storage_registry: PluginRegistry[StorageConfig, BlobStorage] = PluginRegistry()

# Public API
register_storage = storage_registry.register
build_storage    = storage_registry.create
get_storage      = storage_registry.get
list_storages    = storage_registry.names

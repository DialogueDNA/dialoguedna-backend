from __future__ import annotations
from azure.storage.blob import BlobServiceClient
from app.ports.storage.blob_storage import BlobStorage
from app.state.app_states import StorageState
from app.storage.adapters.azure.azure_blob import AzureBlobAdapter
from app.storage.plugins import register_storage
from app.core.config import StorageConfig

@register_storage("azure_blob")
def build_azure_storage(config: StorageConfig, app_state_storage: StorageState) -> BlobStorage:
    if not getattr(app_state_storage, "azure_blob_service", None):
        if config.azure_conn_str:
            svc = BlobServiceClient.from_connection_string(config.azure_conn_str)
            app_state_storage.azure_account_key = config.azure_key
        else:
            if not (config.azure_account and config.azure_key):
                raise RuntimeError("Azure storage requires either connection string or (account+key).")
            endpoint = f"https://{config.azure_account}.blob.core.windows.net"
            svc = BlobServiceClient(account_url=endpoint, credential=config.azure_key)
            app_state_storage.azure_account_key = config.azure_key
        app_state_storage.azure_blob_service = svc

    adapter = AzureBlobAdapter(app_state_storage.azure_blob_service, public_base=config.azure_public_base)
    adapter._account_key = getattr(app_state_storage, "_azure_account_key", None)
    return adapter
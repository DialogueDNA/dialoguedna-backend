from __future__ import annotations

import gzip
import io
import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import BinaryIO, List, Dict, Any
from azure.storage.blob import (
    BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
)

from app.core.config import StorageConfig
from app.core.constants.storage.azure_constants import MAIN_CONTAINER
from app.interfaces.storage.blob_storage import BlobStorage


class AzureBlobStorage(BlobStorage):
    def __init__(self, service: BlobServiceClient, public_base: str = "", account_key: str | None = None):
        self._svc = service
        self._public_base = public_base.rstrip("/")
        self._account_key = account_key

    @classmethod
    def from_config(cls, cfg: StorageConfig) -> "AzureBlobStorage":
        azure_cfg = cfg.azure
        if getattr(azure_cfg, "connection_string", None):
            svc = BlobServiceClient.from_connection_string(azure_cfg.connection_string)
            account_key = azure_cfg.account_key
        else:
            if not (getattr(azure_cfg, "account_name", None) and getattr(azure_cfg, "account_key", None)):
                raise RuntimeError("Azure storage requires either connection string or (account+key).")
            endpoint = f"https://{azure_cfg.account_name}.blob.core.windows.net"
            svc = BlobServiceClient(account_url=endpoint, credential=azure_cfg.account_key)
            account_key = azure_cfg.account_key
        return cls(svc, public_base=getattr(azure_cfg, "public_base_url", "") or "", account_key=account_key)

    def upload(self, container: str, blob: str, data: bytes | BinaryIO, *, content_type: str | None = None) -> str:
        stream = io.BytesIO(data) if isinstance(data, (bytes, bytearray)) else data
        blob_client = self._svc.get_blob_client(container=container, blob=blob)
        content_settings = ContentSettings(content_type=content_type) if content_type else None
        blob_client.upload_blob(stream, overwrite=True, content_settings=content_settings)
        return self.url(container, blob, public=False)

    def download(self, container: str, blob: str) -> bytes:
        blob_client = self._svc.get_blob_client(container=container, blob=blob)
        return blob_client.download_blob().readall()

    def delete(self, container: str, blob: str) -> None:
        blob_client = self._svc.get_blob_client(container=container, blob=blob)
        blob_client.delete_blob()

    def url(self, container: str, blob: str, *, public: bool = False) -> str:
        if public and self._public_base:
            return f"{self._public_base}/{container}/{blob}"
        return self._svc.get_blob_client(container=container, blob=blob).url

    def generate_sas_url(self, container: str, blob: str, *, expiry_seconds: int = 3600) -> str:
        account_name = self._svc.account_name
        if not hasattr(self, "_account_key") or not self._account_key:
            raise RuntimeError("AzureBlobAdapter: account key missing for SAS generation.")

        expires_on = datetime.utcnow() + timedelta(seconds=expiry_seconds)
        sas = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=blob,
            account_key=self._account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expires_on,
        )

        base_url = self._svc.get_blob_client(container=container, blob=blob).url
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}{sas}"

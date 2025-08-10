# app/storage/adapters/azure_blob.py
from __future__ import annotations
import io
from datetime import timedelta
from typing import BinaryIO
from azure.storage.blob import (
    BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
)
from app.ports.storage.blob_storage import BlobStorage

class AzureBlobAdapter(BlobStorage):
    def __init__(self, service: BlobServiceClient, public_base: str = ""):
        self._svc = service
        self._public_base = public_base.rstrip("/")

    def upload(self, container: str, blob: str, data: bytes | BinaryIO, *, content_type: str | None = None) -> str:
        if isinstance(data, (bytes, bytearray)):
            stream = io.BytesIO(data)
        else:
            stream = data  # BinaryIO
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

        if not hasattr(self, "_account_key"):
            raise RuntimeError("AzureBlobAdapter: account key missing for SAS generation.")

        sas = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=blob,
            account_key=self._account_key,
            permission=BlobSasPermissions(read=True),
            expiry=timedelta(seconds=expiry_seconds),
        )

        base_url = self._svc.get_blob_client(container=container, blob=blob).url
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}{sas}"

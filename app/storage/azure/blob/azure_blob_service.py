# app/storage/azure/blob/azure_blob_service.py

# Thin service that the rest of the app calls. Keeps API clear:
# - upload_audio_file(...)  -> AUDIO from FastAPI UploadFile
# - upload_file(...)        -> CONTENT from local path (back-compat name)
# - upload_content_file(...) -> CONTENT with explicit MIME

from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.storage.azure.blob.azure_blob_deleter import AzureBlobDeleter
from app.storage.azure.blob.azure_blob_fetcher import AzureBlobFetcher
from app.storage.azure.blob.azure_blob_uploader import AzureBlobUploader


class AzureBlobService:
    def __init__(self):
        self.uploader = AzureBlobUploader()
        self.deleter = AzureBlobDeleter()
        self.fetcher = AzureBlobFetcher()

    # === Upload ===
    def upload_audio_file(self, file: UploadFile, blob_name: str) -> str:
        """Audio path: receives UploadFile, converts if needed, sets audio/wav."""
        return self.uploader.upload_audio_file(file, blob_name)

    def upload_file(self, tmp_path: Path, blob_path: str) -> str:
        """Generic content upload (no audio conversion)."""
        return self.uploader.upload_content_file(tmp_path, blob_path)

    # === CONTENT (local path) — with explicit MIME ===
    def upload_content_file(self, file_path: Path, blob_name: str, content_type: Optional[str]) -> str:
        """Generic content upload with explicit Content-Type (e.g. application/json)."""
        return self.uploader.upload_content_file(Path(file_path), blob_name, content_type)

    # === Fetch ===
    def generate_sas_url(self, blob_name: str) -> str:
        """Generate a temporary SAS URL for accessing a blob."""
        return self.fetcher.generate_sas_url(blob_name)

    def blob_exists(self, blob_name: str) -> bool:
        """Check if a blob exists."""
        return self.fetcher.blob_exists(blob_name)

    # === Delete ===
    def delete_blob(self, blob_name: str):
        """Delete a blob by name."""
        return self.deleter.delete_blob(blob_name)

    def delete_blob_from_url(self, url: str):
        """Delete a blob using its full SAS URL."""
        return self.deleter.delete_blob_from_url(url)

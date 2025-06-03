from pathlib import Path
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
    def upload_uploadfile(self, file: UploadFile, blob_name: str, convert_to_wav: bool = True) -> None:
        """Upload a FastAPI UploadFile to Azure."""
        return self.uploader.upload_uploadfile(file, blob_name, convert_to_wav)

    def upload_file(self, tmp_path, blob_path):
        return self.uploader.uploadfile(tmp_path, blob_path)

    # === Fetch ===
    def generate_sas_url(self, blob_name: str) -> str:
        """Generate a temporary SAS URL for accessing a blob."""
        return self.fetcher.generate_sas_url(blob_name)

    def blob_exists(self, blob_name: str) -> bool:
        """Check if a blob exists (requires implementation in AzureFetcher)."""
        return self.fetcher.blob_exists(blob_name)

    # === Delete ===
    def delete_blob(self, blob_name: str):
        """Delete a blob by name."""
        return self.deleter.delete_blob(blob_name)

    def delete_blob_from_url(self, url: str):
        """Delete a blob using its full SAS URL."""
        return self.deleter.delete_blob_from_url(url)
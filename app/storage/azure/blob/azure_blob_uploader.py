# app/storage/azure/azure_blob_loader.py

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile

from app.storage.azure.azure_uploader import AzureUploader


class AzureBlobUploader:
    def __init__(self):
        self.uploader = AzureUploader()

    def upload_path(self, file_path: Path, blob_name: str) -> str:
        """
        Upload a file from a local path to Azure Blob Storage.
        Returns the blob name (path inside container).
        """
        self.uploader.upload_file(file_path, blob_name=blob_name)
        return blob_name

    def uploadfile(self, tmp_path: Path, blob_path: str) -> str:
        """
        Upload a file from a local temporary path to Azure Blob Storage
        and return the blob path.
        """
        if not tmp_path.exists():
            raise FileNotFoundError(f"File not found: {tmp_path}")

        self.uploader.upload_file(tmp_path, blob_path)
        return blob_path

    def upload_uploadfile(self, file: UploadFile, blob_name: str, convert_to_wav: bool = True) -> None:
        """
        Accepts a FastAPI UploadFile, saves to a temp file,
        optionally converts to WAV, then uploads to Azure.
        """
        tmp_path = None
        converted_path = None

        try:
            # Save the UploadFile to a temporary file
            extension = Path(file.filename).suffix or ".tmp"
            with NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)

            file_path = tmp_path

            # Optionally convert to WAV format before uploading
            if convert_to_wav:
                converted_path = self.uploader.convert_to_wav(tmp_path)
                file_path = converted_path

            self.uploader.upload_file(file_path, blob_name=blob_name)
            return blob_name

        finally:
            # Clean up temp files
            for path in [tmp_path, converted_path]:
                if path and path.exists():
                    try:
                        path.unlink()
                    except Exception as e:
                        print(f"⚠️ Failed to delete temp file: {e}")
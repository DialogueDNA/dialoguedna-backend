import shutil
from pathlib import Path

from fastapi import UploadFile

from app.services.azure_uploader import AzureUploader
from tempfile import NamedTemporaryFile

from app.core.config import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINER_NAME,
    TRANSCRIPTS_DIR,
)

class DBLoader:
    def __init__(self):
        self.uploader = AzureUploader(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )

    def load_audio(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        print("☁️ Uploading audio to Azure...")
        return self.uploader.upload_file_and_get_sas(audio_path, blob_name=audio_path.name)

    def load_audio_from_file(self, file: UploadFile) -> str:
        tmp_path = None

        try:
            # 🔍 Detect extension from original filename
            extension = Path(file.filename).suffix or ".wav"

            # 💾 Save UploadFile to temp file
            with NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)

            print(f"☁️ Uploading audio '{file.filename}' to Azure...")
            sas_url = self.uploader.upload_file_and_get_sas(tmp_path, blob_name=f"{tmp_path.stem}{extension}")
            if not sas_url:
                raise ValueError("Azure upload failed — no SAS URL returned")

            return sas_url

        finally:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception as e:
                    print(f"⚠️ Failed to delete temp file: {e}")
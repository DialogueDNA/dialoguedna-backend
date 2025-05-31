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

    def load_audio_from_file(self, file: UploadFile,blob_name: str) -> str:
        tmp_path = None

        try:
            extension = Path(file.filename).suffix or ".tmp"

            # 💾 Save UploadFile to temp file
            with NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)

            # Convert to WAV format using pydub (ensures valid format)
            wav_path = self.uploader.convert_to_wav(tmp_path)

            print(f"☁️ Uploading audio '{file.filename}' to Azure at '{blob_name}'...")

            # Upload the file to Azure using the provided blob name
            sas_url = self.uploader.upload_file_and_get_sas(wav_path, blob_name=blob_name)
            print(sas_url)
            if not sas_url:
                raise ValueError("Azure upload failed — no SAS URL returned")

            return sas_url


        finally:
            for path in [tmp_path, wav_path]:
                if path and path.exists():
                    try:
                        path.unlink()
                    except Exception as e:
                        print(f"⚠️ Failed to delete temp file: {e}")

import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from tempfile import NamedTemporaryFile

from app.services.infrastructure.azure_uploader import AzureUploader
from app.core.config import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINER_NAME,
)

class DBLoader:
    def __init__(self):
        self.uploader = AzureUploader(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )

    # def load_audio(self, audio_path: str) -> str:
    #     audio_path = Path(audio_path)
    #     print("☁️ Uploading audio to Azure...")
    #     return self.uploader.upload_file_and_get_sas(audio_path, blob_name=audio_path.name)

    def load_audio(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        print("☁️ Uploading audio to Azure...")
        sas_url, blob_name = self.uploader.upload_file_and_get_sas(audio_path, blob_name=audio_path.name);
        return sas_url

    def load_audio_from_file(self, file: UploadFile) -> tuple[str, str]:
        tmp_path = None
        wav_path = None  # 🔧 Initialize wav_path to avoid UnboundLocalError

        try:
            extension = Path(file.filename).suffix or ".tmp"

            # 💾 Save UploadFile to temp file
            with NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)

            # Convert to WAV format using pydub (ensures valid format)
            wav_path = self.uploader.convert_to_wav(tmp_path)

            # 🆔 Generate a unique session ID
            session_id = str(uuid.uuid4())

            # 📁 Set blob name to "sessions/{session_id}/audio.wav"
            blob_name = f"{session_id}/audio.wav"

            print(f"☁️ Uploading audio '{file.filename}' to Azure...")

            # Upload the file to Azure using the provided blob name
            sas_url,blob_name = self.uploader.upload_file_and_get_sas(wav_path, blob_name=blob_name)
            #folder_sas_url = f"{AZURE_CONTAINER_URL}/{session_id}"

            print(sas_url)
            if not sas_url:
                raise ValueError("Azure upload failed — no SAS URL returned")

            return session_id, sas_url

        finally:
            for path in [tmp_path, wav_path]:
                if path and path.exists():
                    try:
                        path.unlink()
                    except Exception as e:
                        print(f"⚠️ Failed to delete temp file: {e}")

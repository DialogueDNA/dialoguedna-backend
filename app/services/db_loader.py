from pathlib import Path
from app.services.azure_uploader import AzureUploader
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
        sas_url = self.uploader.upload_file_and_get_sas(audio_path)
        return sas_url
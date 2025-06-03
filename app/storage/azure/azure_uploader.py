from pathlib import Path
from azure.storage.blob import BlobServiceClient, ContentSettings
from pydub import AudioSegment

from app.core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME

class AzureUploader:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container = self.client.get_container_client(AZURE_CONTAINER_NAME)

    def upload_file(self, file_path: Path, blob_name: str):
        """Uploads a local file to Azure Blob Storage."""
        with open(file_path, "rb") as file:
            self.container.upload_blob(
                name=blob_name,
                data=file,
                overwrite=True,
                content_settings=ContentSettings(content_type=self._guess_mime(file_path))
            )

    def convert_to_wav(self, file_path: Path) -> Path:
        """Converts an audio file to .wav format using pydub and returns the new path."""
        wav_path = file_path.with_suffix(".wav")
        audio = AudioSegment.from_file(file_path)
        audio.export(wav_path, format="wav")
        return wav_path

    def _guess_mime(self, file_path: Path) -> str:
        if file_path.suffix.lower() == ".wav":
            return "audio/wav"
        if file_path.suffix.lower() == ".mp3":
            return "audio/mpeg"
        return "application/octet-stream"
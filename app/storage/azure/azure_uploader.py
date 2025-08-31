# app/storage/azure/azure_uploader.py

from pathlib import Path
from azure.storage.blob import BlobServiceClient, ContentSettings

from app.core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
from app.media.audio_utils import ensure_transcription_ready  # makes sure audio is Azure-friendly


class AzureUploader:
    def __init__(self):
        # Create a connection to Azure Blob Storage
        self.client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container = self.client.get_container_client(AZURE_CONTAINER_NAME)

    def upload_file(self, file_path: Path, blob_name: str):
        """
        Converts audio to Azure-compatible format (WAV, PCM s16, 16kHz, mono) if needed,
        uploads it with correct Content-Type, and deletes temporary file afterwards.
        """
        file_path = Path(file_path)

        # 1) Ensure the file is in the correct transcription-ready format
        fixed_path = ensure_transcription_ready(file_path)
        is_temp = (fixed_path != file_path)  # True if a converted temporary file was created

        try:
            with open(fixed_path, "rb") as f:
                self.container.upload_blob(
                    name=blob_name,
                    data=f,
                    overwrite=True,
                    content_settings=ContentSettings(content_type="audio/wav"),  # Explicitly set MIME type
                )
        finally:
            # 2) Clean up temporary file if one was created
            if is_temp:
                try:
                    fixed_path.unlink(missing_ok=True)
                except Exception:
                    # If deletion fails, ignore silently (could log here if desired)
                    pass

    # Legacy method (no longer needed, kept only for backward compatibility)
    def convert_to_wav(self, file_path: Path) -> Path:
        """
        DEPRECATED: Conversion is now handled by ensure_transcription_ready inside upload_file.
        This method remains only to avoid breaking old code that might still call it.
        """
        return file_path.with_suffix(".wav")

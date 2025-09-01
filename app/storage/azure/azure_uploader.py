# app/storage/azure/azure_uploader.py

from pathlib import Path
from typing import Optional
from azure.storage.blob import BlobServiceClient, ContentSettings

from app.core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
from app.media.audio_utils import ensure_transcription_ready  # makes sure audio is Azure-friendly


class AzureUploader:
    def __init__(self):
        # Create a connection to Azure Blob Storage
        self.client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container = self.client.get_container_client(AZURE_CONTAINER_NAME)


    # === 1) AUDIO ===
    def upload_audio_file(self, file_path: Path, blob_name: str)->str:
        """
               Convert to WAV/PCM s16/16kHz/mono if needed, then upload with audio/wav.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

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

        return blob_name


    # === 2) GENERIC CONTENT (JSON/TXT/וכו') ===
    def upload_content_file(self, file_path: Path, blob_name: str, content_type: Optional[str] = None) -> str:
        """
        Upload file as-is (no conversion). Optionally set Content-Type.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        cs = ContentSettings(content_type=content_type) if content_type else None
        with open(file_path, "rb") as f:
            self.container.upload_blob(
                name=blob_name,
                data=f,
                overwrite=True,
                content_settings=cs,
            )
        return blob_name





#todo: delete if not needed

    # Legacy method (no longer needed, kept only for backward compatibility)
    def convert_to_wav(self, file_path: Path) -> Path:
        """
        DEPRECATED: Conversion is now handled by ensure_transcription_ready inside upload_file.
        This method remains only to avoid breaking old code that might still call it.
        """
        return file_path.with_suffix(".wav")

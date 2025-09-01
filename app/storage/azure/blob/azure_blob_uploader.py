# app/storage/azure/blob/azure_blob_uploader.py

from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.storage.azure.azure_uploader import AzureUploader
from app.media.audio_utils import save_upload_to_visible_tmp  # RAW -> app/temp_converted_audio_file/src/...


class AzureBlobUploader:
    def __init__(self):
        self.uploader = AzureUploader()


    # ===== CONTENT (prev: upload_path) =====
    def upload_content_file(self, file_path: Path, blob_name: str,content_type: Optional[str] = None) -> str:
        """
        Upload a generic content file from a local path *as-is* (no audio conversion).
        Use this for JSON/TXT and any non-audio assets.

        Args:
            file_path: Local filesystem path to the already-written file.
            blob_name: Destination blob path (e.g., '{session_id}/transcript.json').
            content_type: Explicit MIME to set on the blob (e.g., 'application/json',
                          'text/plain; charset=utf-8'). If None, Azure will infer.

        Returns:
            The blob_name that was uploaded.

        Raises:
            FileNotFoundError: If file_path does not exist.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # No conversion here; we just push the bytes with the provided MIME (if any)
        self.uploader.upload_content_file(file_path, blob_name=blob_name, content_type=content_type)
        return blob_name










    # ===== AUDIO (prev: upload_uploadfile) =====
    def upload_audio_file(self, file: UploadFile, blob_name: str) -> str:
        """
              Upload audio that arrives as FastAPI UploadFile.
              Steps:
                1) Persist the incoming stream to a visible, stable temp path (for debugging).
                2) Delegate to AzureUploader.upload_audio_file(...) which:
                   - Converts to WAV/PCM s16/16kHz/mono if needed.
                   - Uploads with Content-Type 'audio/wav'.
                3) Optionally delete the RAW temp file (kept for now for easier debugging).

              Args:
                  file: FastAPI UploadFile received from the client.
                  blob_name: Destination blob path (e.g., '{session_id}/audio.wav').

              Returns:
                  The blob_name that was uploaded.
              """
        # Save RAW to a visible folder (for debugging/traceability)
        raw_path: Path = save_upload_to_visible_tmp(file)  # e.g., app/temp_converted_audio_file/src/...

        try:
            # This performs conversion (if needed) and uploads with correct audio MIME
            self.uploader.upload_audio_file(raw_path, blob_name=blob_name)
            return blob_name
        finally:

            #todo: decide if we want to delete the raw file or not

            # 3) Optional cleanup of RAW file after upload
            # Uncomment to enable automatic deletion of the RAW file:
            #
            # try:
            #     raw_path.unlink(missing_ok=True)
            # except Exception as e:
            #     print(f"⚠️ Failed to delete RAW file: {e}")
            pass



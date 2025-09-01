#app/storage/session_storage.py
import json
from uuid import uuid4
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.storage.azure.blob.azure_blob_service import AzureBlobService

VISIBLE_TMP_DIR = Path("app/temp_converted_audio_file/content")  # visible, debuggable


class SessionStorage:
    def __init__(self):
        self.azure = AzureBlobService()

    # === Upload ===

    def store_audio(self, session_id: str, file: UploadFile) -> str:
        """Upload incoming audio via the AUDIO path (converts + audio/wav)."""
        blob_path = f"{session_id}/audio.wav"
        self.azure.upload_audio_file(file, blob_path)  # was: upload_uploadfile
        return blob_path

    def store_transcript(self, session_id: str, content: list[dict[str, Any]]) -> str:
        """Persist transcript JSON with proper suffix + MIME."""
        return self._store_json(session_id, "transcript", content)

    def store_summary(self, session_id: str, content: str) -> str:
        """Persist summary TXT with proper suffix + MIME."""
        return self._store_text(session_id, "summary", content)

    def store_emotions(self, session_id: str, content: list[dict[str, Any]]) -> str:
        """Persist emotions JSON with proper suffix + MIME."""
        return self._store_json(session_id, "emotions", content)

    def _store_text(self, session_id: str, name: str, content: str) -> str:
        """Write a temp .txt locally, then upload as text/plain (no audio conversion)."""
        blob_path = f"{session_id}/{name}.txt"
        tmp_path = self._write_temp_file(content, suffix=".txt")
        self.azure.upload_content_file(tmp_path, blob_path, "text/plain; charset=utf-8")
        tmp_path.unlink(missing_ok=True)
        return blob_path

    def _store_json(self, session_id: str, name: str, content: dict | list) -> str:
        """Write a temp .json locally, then upload as application/json (no audio conversion)."""
        blob_path = f"{session_id}/{name}.json"
        tmp_path = self._write_temp_file(json.dumps(content, indent=2,ensure_ascii=False), suffix=".json")
        self.azure.upload_content_file(tmp_path, blob_path, "application/json")
        tmp_path.unlink(missing_ok=True)
        return blob_path

    def _write_temp_file(self, content: str, suffix: str = ".tmp") -> Path:
        """
        Write content to a visible, stable temp file (Windows-friendly).
        File is NOT auto-deleted here; caller deletes after successful upload.
        """
        VISIBLE_TMP_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = VISIBLE_TMP_DIR / f"{uuid4().hex}{suffix}"
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return tmp_path

    # === Fetch ===

    def generate_sas_url(self, blob_path: str) -> str:
        return self.azure.generate_sas_url(blob_path)

    def blob_exists(self, blob_path: str) -> bool:
        return self.azure.blob_exists(blob_path)

    # === Delete ===

    def delete_audio(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/audio.wav")

    def delete_transcript(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/transcript.json")  # add suffix

    def delete_summary(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/summary.txt")      # add suffix

    def delete_emotions(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/emotions.json")    # add suffix

    def delete_all(self, session_id: str):
        self.delete_audio(session_id)
        self.delete_transcript(session_id)
        self.delete_summary(session_id)
        self.delete_emotions(session_id)
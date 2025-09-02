#app/storage/session_storage.py
import json
from uuid import uuid4
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.storage.azure.blob.azure_blob_service import AzureBlobService

VISIBLE_TMP_DIR = Path("temp_converted_audio_file/content")  # visible, debuggable


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
        local_path = self._write_fixed_file("summary.txt", content)
        blob_path = f"{session_id}/{name}"
        self.azure.upload_content_file(local_path, blob_path, "text/plain; charset=utf-8")
        local_path.unlink(missing_ok=True)
        return blob_path

    def _store_json(self, session_id: str, name: str, content: dict | list) -> str:
        """Write a temp .json locally, then upload as application/json (no audio conversion)."""
        local_filename = "transcript.json" if name == "transcript" else "emotion.json"  # לפי בקשתך
        local_path = self._write_fixed_file(local_filename, json.dumps(content, indent=2, ensure_ascii=False))
        blob_path = f"{session_id}/{name}"  # ב-Azure נשאר "transcript.json" / "emotions.json"
        self.azure.upload_content_file(local_path, blob_path, "application/json")
        local_path.unlink(missing_ok=True)
        return blob_path

    def _write_fixed_file(self, filename: str, content: str) -> Path:
        """Write to a visible, stable path with a fixed filename."""
        VISIBLE_TMP_DIR.mkdir(parents=True, exist_ok=True)
        path = VISIBLE_TMP_DIR / filename
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return path

    # === Fetch ===

    def generate_sas_url(self, blob_path: str) -> str:
        return self.azure.generate_sas_url(blob_path)

    def blob_exists(self, blob_path: str) -> bool:
        return self.azure.blob_exists(blob_path)

    # === Delete ===

    def delete_audio(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/audio.wav")

    def delete_transcript(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/transcript")
        self.azure.delete_blob(f"{session_id}/transcript.json")

    def delete_summary(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/summary")
        self.azure.delete_blob(f"{session_id}/summary.txt")

    def delete_emotions(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/emotions")
        self.azure.delete_blob(f"{session_id}/emotions.json")

    def delete_all(self, session_id: str):
        self.delete_audio(session_id)
        self.delete_transcript(session_id)
        self.delete_summary(session_id)
        self.delete_emotions(session_id)
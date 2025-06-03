import json
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from tempfile import NamedTemporaryFile

from app.storage.azure.blob.azure_blob_service import AzureBlobService


class SessionStorage:
    def __init__(self):
        self.azure = AzureBlobService()

    # === Upload ===

    def store_audio(self, session_id: str, file: UploadFile) -> str:
        blob_path = f"{session_id}/audio.wav"
        self.azure.upload_uploadfile(file, blob_path, convert_to_wav=True)
        return blob_path

    def store_transcript(self, session_id: str, content:  list[dict[str, Any]]) -> str:
        return self._store_json(session_id, "transcript", content)

    def store_summary(self, session_id: str, content: str) -> str:
        return self._store_text(session_id, "summary", content)

    def store_emotions(self, session_id: str, content: list[dict[str, Any]]) -> str:
        return self._store_json(session_id, "emotions", content)

    def _store_text(self, session_id: str, name: str, content: str) -> str:
        blob_path = f"{session_id}/{name}"
        tmp_path = self._write_temp_file(content, suffix=".txt")
        self.azure.upload_file(tmp_path, blob_path)
        tmp_path.unlink(missing_ok=True)
        return blob_path

    def _store_json(self, session_id: str, name: str, content: dict | list) -> str:
        blob_path = f"{session_id}/{name}"
        tmp_path = self._write_temp_file(json.dumps(content, indent=2), suffix=".json")
        self.azure.upload_file(tmp_path, blob_path)
        tmp_path.unlink(missing_ok=True)
        return blob_path

    def _write_temp_file(self, content: str, suffix: str = ".tmp") -> Path:
        with NamedTemporaryFile(delete=False, suffix=suffix, mode="w", encoding="utf-8") as tmp:
            tmp.write(content)
            return Path(tmp.name)

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

    def delete_summary(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/summary")

    def delete_emotions(self, session_id: str):
        self.azure.delete_blob(f"{session_id}/emotions")

    def delete_all(self, session_id: str):
        self.delete_audio(session_id)
        self.delete_transcript(session_id)
        self.delete_summary(session_id)
        self.delete_emotions(session_id)
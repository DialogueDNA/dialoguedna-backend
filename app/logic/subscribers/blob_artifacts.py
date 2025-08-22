from __future__ import annotations

import json
from dataclasses import asdict
from typing import List, Dict, Any, Optional

from app.interfaces.db.domains.sessions_repo import SessionsRepo
from app.logic.subscribers.base import BaseListener
from app.logic.events import TranscriptionEvent, EmotionsEvent, SummaryEvent

class SessionsRepoSubscriber(BaseListener):
    """
    Uploads artifacts to storage and writes their URLs back into the session record.
    Keys scheme: sessions/{sid}/transcript.json, emotions.json, summary.json
    """

    def __init__(self, sessions_repo: SessionsRepo, base_prefix: str = "sessions"):
        self._listener = sessions_repo
        self.base = base_prefix.rstrip("/")

    def on_transcription_ready(self, e: TranscriptionEvent) -> None:
        path = f"{self.base}/{e.session_id}/transcript.json"
        payload = [asdict(seg) for seg in e.segments]
        url = self._put_json_and_get_url(path, payload)
        if url:
            self._listener.update(e.session_id, {"transcript_url": url})

    def on_emotions_ready(self, e: EmotionsEvent) -> None:
        path = f"{self.base}/{e.session_id}/emotions.json"
        payload = [asdict(seg) for seg in e.emotions]
        url = self._put_json_and_get_url(path, payload)
        if url:
            app.database.sessions_repo.update(e.session_id, {"emotions_url": url})

    def on_summary_ready(self, e: SummaryEvent) -> None:
        key = f"{self.base}/{e.session_id}/summary.json"
        url = self._put_json_and_get_url(key, e.summary)
        if url:
            app.database.sessions_repo.update(e.session_id, {"summary_url": url})

    # ------------ shared utility (optional) ------------
    def _put_json_and_get_url(self, path: str, some_json: List[Dict[str, Any]]) -> Optional[str]:
        """
        Store JSON via the configured storage adapter and return a URL if supported.
        This mirrors the previous helper logic, now reusable by multiple listeners.
        """
        data = json.dumps(some_json, ensure_ascii=False).encode("utf-8")

        if hasattr(client, "put_json"):
            return client.put_json(key, obj)

        if hasattr(client, "put_bytes") and hasattr(client, "get_url"):
            client.put_bytes(key, data, content_type="application/json")
            return client.get_url(key)

        if hasattr(client, "put_file") and hasattr(client, "get_url"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
                f.write(data)
                tmp = f.name
            try:
                client.put_file(key, tmp, content_type="application/json")
                return client.get_url(key)
            finally:
                try:
                    os.remove(tmp)
                except Exception:
                    pass

        return None
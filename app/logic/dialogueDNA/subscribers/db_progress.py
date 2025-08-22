from __future__ import annotations

from typing import Dict, Any

import app.core.constants.db.supabase_constants as db_constants
from app.interfaces.db.domains.sessions_repo import SessionsRepo
from app.logic.dialogueDNA.subscribers.base import BaseListener
from app.logic.dialogueDNA.events import StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, CompletedEvent, FailedEvent

class DBProgressSubscriber(BaseListener):
    """Updates the sessions_repo with status/progress and optional inline data."""

    def __init__(self, repo: SessionsRepo, inline_save: bool = False):
        self._listener = repo
        self.inline = inline_save

    def on_stage(self, e: StageEvent) -> None:
        self._listener.update(e.session_id, {"status": e.stage, "status_detail": e.detail})

    def on_transcription_ready(self, e: TranscriptionEvent) -> None:
        patch: Dict[str, Any] = {db_constants.SESSIONS_COLUMN_STATUS: db_constants.SESSION_STATUS_COMPLETED}
        if self.inline:
            patch["transcript"] = e.segments
        self._listener.update(e.session_id, patch)

    def on_emotions_ready(self, e: EmotionsEvent) -> None:
        patch: Dict[str, Any] = {"status": "emotions_ready"}
        if self.inline:
            patch["emotions"] = e.emotions
        self._listener.update(e.session_id, patch)

    def on_summary_ready(self, e: SummaryEvent) -> None:
        patch: Dict[str, Any] = {"status": "summary_ready"}
        if self.inline:
            patch["summary"] = e.summary
        self._listener.update(e.session_id, patch)

    def on_completed(self, e: CompletedEvent) -> None:
        self._listener.update(e.session_id, {"status": "ready"})

    def on_failed(self, e: FailedEvent) -> None:
        self._listener.update(e.session_id, {"status": "failed", "error": e.error})

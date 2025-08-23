from __future__ import annotations
from typing import Any, Dict
from app.logic.dialogueDNA.events.subscribers.base import BaseListener
from app.logic.dialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.dialogueDNA.events import StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, CompletedEvent, FailedEvent

class DBProgressSubscriber(BaseListener):
    def __init__(self, inline_save: bool = False):
        self.inline = inline_save

    def on_stage(self, e: StageEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {"status": e.stage, "status_detail": e.detail})

    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None:
        patch: Dict[str, Any] = {"status": "transcript_ready"}
        if self.inline: patch["transcript"] = e.segments
        ctx.sessions.update(ctx.session_id, patch)

    def on_emotions_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None:
        patch: Dict[str, Any] = {"status": "emotions_ready"}
        if self.inline: patch["emotions"] = e.emotions
        ctx.sessions.update(ctx.session_id, patch)

    def on_summary_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None:
        patch: Dict[str, Any] = {"status": "summary_ready"}
        if self.inline: patch["summary"] = e.summary
        ctx.sessions.update(ctx.session_id, patch)

    def on_completed(self, e: CompletedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {"status": "ready"})

    def on_failed(self, e: FailedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {"status": "failed", "error": e.error})

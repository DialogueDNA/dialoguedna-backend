from __future__ import annotations

from dataclasses import asdict

from app.core.constants.db.supabase_constants import SessionColumn
from app.logic.dialogueDNA.events.subscribers.base import BaseListener
from app.logic.dialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.dialogueDNA.events import TranscriptionEvent, EmotionsEvent, SummaryEvent

class BlobArtifactsSubscriber(BaseListener):
    def __init__(self, base_prefix: str = "sessions"):
        self.base = base_prefix.rstrip("/")

    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        container = f"{self.base}/{ctx.session_id}"
        blob = "transcript.json"
        payload = [asdict(text_segment) for text_segment in e.segments]
        url = ctx.artifacts.put_json_get_url(container=container, blob=blob, some_json=payload)
        if url:
            ctx.sessions.update(ctx.session_id, {
                SessionColumn.transcript_url: url
            })

    def on_emotion_analyzation_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        container = f"{self.base}/{ctx.session_id}"
        blob = "emotions.json"
        payload = [asdict(text_segment) for text_segment in e.emotions]
        url = ctx.artifacts.put_json_get_url(container=container, blob=blob, some_json=payload)
        if url:
            ctx.sessions.update(ctx.session_id, {
                SessionColumn.emotion_breakdown_url: url
            })

    def on_summarization_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        container = f"{self.base}/{ctx.session_id}"
        blob = "summary.json"
        payload = [asdict(e.summary)]
        url = ctx.artifacts.put_json_get_url(container=container, blob=blob, some_json=payload)
        if url:
            ctx.sessions.update(ctx.session_id, {
                SessionColumn.summary_url: url
            })


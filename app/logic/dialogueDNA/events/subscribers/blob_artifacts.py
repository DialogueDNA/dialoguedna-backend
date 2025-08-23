from __future__ import annotations

from dataclasses import asdict

from app.logic.dialogueDNA.events.subscribers.base import BaseListener
from app.logic.dialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.dialogueDNA.events import TranscriptionEvent, EmotionsEvent, SummaryEvent

class BlobArtifactsSubscriber(BaseListener):
    def __init__(self, base_prefix: str = "sessions"):
        self.base = base_prefix.rstrip("/")

    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        key = f"{self.base}/{e.session_id}/transcript.json"
        payload = [asdict(text_segment) for text_segment in e.segments]
        url = ctx.artifacts.put_json_get_url(key, payload)
        if url:
            ctx.sessions.update(e.session_id, {"status": "transcript_ready", "transcript_url": url})

    def on_emotions_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        key = f"{self.base}/{e.session_id}/emotions.json"
        payload = [asdict(text_segment) for text_segment in e.emotions]
        url = ctx.artifacts.put_json_get_url(key, payload)
        if url:
            ctx.sessions.update(e.session_id, {"status": "emotions_ready", "emotions_url": url})

    def on_summary_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        key = f"{self.base}/{e.session_id}/summary.json"
        payload = [asdict(e.summary)]
        url = ctx.artifacts.put_json_get_url(key, payload)
        if url:
            ctx.sessions.update(e.session_id, {"status": "summary_ready", "summary_url": url})

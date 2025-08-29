from __future__ import annotations
from dataclasses import asdict

from app.core.constants.db.supabase_constants import SessionColumn
from app.core.constants.storage.azure_constants import (
    MAIN_CONTAINER, SESSION_TRANSCRIPT_PATH, SESSION_EMOTIONS_PATH, SESSION_SUMMARY_PATH
)
from app.logic.DialogueDNA.events.subscribers.base import BaseListener
from app.logic.DialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.DialogueDNA.events import TranscriptionEvent, EmotionsEvent, SummaryEvent

class BlobArtifactsSubscriber(BaseListener):
    def __init__(self):
        pass

    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        container = MAIN_CONTAINER
        blob = f"{ctx.session_id}/{SESSION_TRANSCRIPT_PATH}"
        payload = [asdict(text_segment) for text_segment in e.segments]
        url = ctx.artifacts.put_json_get_url(container=container, blob=blob, some_json=payload)
        if url:
            ctx.sessions.update(ctx.session_id, {SessionColumn.transcript_url: url})

    def on_emotion_analyzation_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        container = MAIN_CONTAINER
        blob = f"{ctx.session_id}/{SESSION_EMOTIONS_PATH}"
        payload = [asdict(seg) for seg in e.emotions]
        url = ctx.artifacts.put_json_get_url(container=container, blob=blob, some_json=payload)
        if url:
            ctx.sessions.update(ctx.session_id, {SessionColumn.emotion_breakdown_url: url})

    def on_summarization_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None:
        if not ctx.artifacts: return
        container = MAIN_CONTAINER
        blob = f"{ctx.session_id}/{SESSION_SUMMARY_PATH}"
        payload = [asdict(e.summary)]
        url = ctx.artifacts.put_json_get_url(container=container, blob=blob, some_json=payload)
        if url:
            ctx.sessions.update(ctx.session_id, {SessionColumn.summary_url: url})

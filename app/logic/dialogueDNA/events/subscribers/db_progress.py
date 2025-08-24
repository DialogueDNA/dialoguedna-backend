from __future__ import annotations

from app.core.constants.db.supabase_constants import SessionColumn, SessionStatus
from app.logic.dialogueDNA.events.subscribers.base import BaseListener
from app.logic.dialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.dialogueDNA.events import StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, \
    FailedEvent, QueuedEvent, StoppedEvent, ProcessingEvent


class DBProgressSubscriber(BaseListener):
    def __init__(self, inline_save: bool = False):
        self.inline = inline_save

    def on_stage(self, e: StageEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.session_status: e.stage
        })
    def on_transcription_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.transcript_status: SessionStatus.queued
        })
    def on_transcription_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.transcript_status: SessionStatus.stopped
        })
    def on_transcription_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.transcript_status: SessionStatus.progressing
        })
    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.transcript_status: SessionStatus.completed
        })
    def on_transcription_failed(self, e: FailedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.transcript_status: SessionStatus.failed
        })
    def on_emotion_analyzation_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.emotion_breakdown_status: SessionStatus.queued
        })
    def on_emotion_analyzation_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.emotion_breakdown_status: SessionStatus.stopped
        })
    def on_emotion_analyzation_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.emotion_breakdown_status: SessionStatus.progressing
        })
    def on_emotion_analyzation_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.emotion_breakdown_status: SessionStatus.completed
        })
    def on_emotion_analyzation_failed(self, e: FailedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.emotion_breakdown_status: SessionStatus.failed
        })
    def on_summarization_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.summary_status: SessionStatus.queued
        })
    def on_summarization_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.summary_status: SessionStatus.stopped
        })
    def on_summarization_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.summary_status: SessionStatus.progressing
        })
    def on_summarization_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.summary_status: SessionStatus.completed
        })
    def on_summarization_failed(self, e: FailedEvent, ctx: PipelineContext) -> None:
        ctx.sessions.update(ctx.session_id, {
            SessionColumn.summary_status: SessionStatus.failed
        })
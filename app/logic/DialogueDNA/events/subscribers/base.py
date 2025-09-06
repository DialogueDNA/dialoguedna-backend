from __future__ import annotations
from app.logic.DialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.DialogueDNA.events import (
    StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, FailedEvent, QueuedEvent, StoppedEvent,
    ProcessingEvent, MetadataEvent, AudioEvent
)
from app.logic.DialogueDNA.interfaces.listeners import PipelineListener


class BaseListener(PipelineListener):
    def on_stage(self, e: StageEvent, ctx: PipelineContext) -> None: pass
    def on_session_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_session_stopped(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_session_processing(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_session_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None: pass
    def on_session_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: pass
    def on_metadata_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_metadata_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None: pass
    def on_metadata_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None: pass
    def on_metadata_ready(self, e: MetadataEvent, ctx: PipelineContext) -> None: pass
    def on_metadata_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: pass
    def on_audio_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_audio_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None: pass
    def on_audio_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None: pass
    def on_audio_ready(self, e: AudioEvent, ctx: PipelineContext) -> None: pass
    def on_audio_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: pass
    def on_transcription_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_transcription_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None: pass
    def on_transcription_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None: pass
    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None: pass
    def on_transcription_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: pass
    def on_emotion_analyzation_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_emotion_analyzation_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None: pass
    def on_emotion_analyzation_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None: pass
    def on_emotion_analyzation_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None: pass
    def on_emotion_analyzation_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: pass
    def on_summarization_queued(self, e: QueuedEvent, ctx: PipelineContext) -> None: pass
    def on_summarization_stopped(self, e: StoppedEvent, ctx: PipelineContext) -> None: pass
    def on_summarization_processing(self, e: ProcessingEvent, ctx: PipelineContext) -> None: pass
    def on_summarization_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None: pass
    def on_summarization_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: pass

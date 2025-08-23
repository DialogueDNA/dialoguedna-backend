from __future__ import annotations
from typing import Protocol
from app.logic.dialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.dialogueDNA.events import (
    StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, CompletedEvent, FailedEvent
)

class PipelineListener(Protocol):
    def on_stage(self, e: StageEvent, ctx: PipelineContext) -> None: ...
    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None: ...
    def on_emotions_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None: ...
    def on_summary_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None: ...
    def on_completed(self, e: CompletedEvent, ctx: PipelineContext) -> None: ...
    def on_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: ...

class BaseListener:
    def on_stage(self, e: StageEvent, ctx: PipelineContext) -> None: pass
    def on_transcription_ready(self, e: TranscriptionEvent, ctx: PipelineContext) -> None: pass
    def on_emotions_ready(self, e: EmotionsEvent, ctx: PipelineContext) -> None: pass
    def on_summary_ready(self, e: SummaryEvent, ctx: PipelineContext) -> None: pass
    def on_completed(self, e: CompletedEvent, ctx: PipelineContext) -> None: pass
    def on_failed(self, e: FailedEvent, ctx: PipelineContext) -> None: pass

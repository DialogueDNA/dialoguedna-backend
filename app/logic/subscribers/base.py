from __future__ import annotations
from typing import Protocol
from app.logic.events import (
    StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, CompletedEvent, FailedEvent
)

class PipelineListener(Protocol):
    """Contract for subscribers interested in pipeline milestones."""
    def on_stage(self, e: StageEvent) -> None: ...
    def on_transcription_ready(self, e: TranscriptionEvent) -> None: ...
    def on_emotions_ready(self, e: EmotionsEvent) -> None: ...
    def on_summary_ready(self, e: SummaryEvent) -> None: ...
    def on_completed(self, e: CompletedEvent) -> None: ...
    def on_failed(self, e: FailedEvent) -> None: ...

class BaseListener:
    _listener = None

    """No-op defaults so implementers can override only what they need."""
    def on_stage(self, e: StageEvent) -> None:                          pass
    def on_transcription_ready(self, e: TranscriptionEvent) -> None:    pass
    def on_emotions_ready(self, e: EmotionsEvent) -> None:              pass
    def on_summary_ready(self, e: SummaryEvent) -> None:                pass
    def on_completed(self, e: CompletedEvent) -> None:                  pass
    def on_failed(self, e: FailedEvent) -> None:                        pass

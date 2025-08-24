from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from app.logic.dialogueDNA.events.subscribers.base import PipelineListener
from app.logic.dialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.dialogueDNA.events import (
    StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, FailedEvent, QueuedEvent, StoppedEvent,
    ProcessingEvent
)

log = logging.getLogger(__name__)

@dataclass
class PipelineReporter:
    dispatch: str = "sync"  # "sync" | "thread"
    _subs: List[Tuple[str, PipelineListener, PipelineContext]] = field(default_factory=list, init=False)
    _executor: Optional[ThreadPoolExecutor] = field(default=None, init=False)

    def __post_init__(self):
        if self.dispatch == "thread":
            self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="pipeline-listener")

    # subscribe with a specific least-privilege context
    def subscribe(self, listener: PipelineListener, ctx: PipelineContext) -> str:
        token = str(uuid4())
        self._subs.append((token, listener, ctx))
        return token

    def unsubscribe(self, token: str) -> bool:
        for i, (t, *_rest) in enumerate(self._subs):
            if t == token:
                self._subs.pop(i)
                return True
        return False

    def clear(self) -> None:
        self._subs.clear()

    # emits
    def stage                           (self, stage: str, detail: Optional[str] = None):   self._emit("on_stage",                          StageEvent(stage, detail))
    def transcription_queued            (self):                                             self._emit("on_transcription_queued",           QueuedEvent())
    def transcription_stopped           (self):                                             self._emit("on_transcription_stopped",          StoppedEvent())
    def transcription_processing        (self):                                             self._emit("on_transcription_processing",       ProcessingEvent())
    def transcription_ready             (self, segments):                                   self._emit("on_transcription_ready",            TranscriptionEvent(segments))
    def transcription_failed            (self, error):                                      self._emit("on_transcription_failed",           FailedEvent(error))
    def emotion_analyzation_queued      (self):                                             self._emit("on_emotion_analyzation_queued",     QueuedEvent())
    def emotion_analyzation_stopped     (self):                                             self._emit("on_emotion_analyzation_stopped",    StoppedEvent())
    def emotion_analyzation_processing  (self):                                             self._emit("on_emotion_analyzation_processing", ProcessingEvent())
    def emotion_analyzation_ready       (self, emotions):                                   self._emit("on_emotion_analyzation_ready",      EmotionsEvent(emotions))
    def emotion_analyzation_failed      (self, error):                                      self._emit("on_emotion_analyzation_failed",     FailedEvent(error))
    def summarization_queued            (self):                                             self._emit("on_summarization_queued",           QueuedEvent())
    def summarization_stopped           (self):                                             self._emit("on_summarization_stopped",          StoppedEvent())
    def summarization_processing        (self):                                             self._emit("on_summarization_processing",       ProcessingEvent())
    def summarization_ready             (self, summary):                                    self._emit("on_summarization_ready",            SummaryEvent(summary))
    def summarization_failed            (self, error):                                      self._emit("on_summarization_failed",           FailedEvent(error))

    def _emit(self, method: str, event: Any) -> None:
        for token, sub, ctx in list(self._subs):
            fn = getattr(sub, method, None)
            if not callable(fn):
                continue
            try:
                if self.dispatch == "thread" and self._executor is not None:
                    self._executor.submit(fn, event, ctx)
                else:
                    fn(event, ctx)
            except Exception as e:
                log.warning("Listener(%s) failed in %s: %s", token, method, e, exc_info=True)

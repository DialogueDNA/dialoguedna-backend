from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from app.interfaces.services.emotions import EmotionAnalyzerBundle
from app.interfaces.services.summary import SummaryOutput
from app.interfaces.services.transcription import TranscriptionOutput
from app.logic.dialogueDNA.subscribers.base import PipelineListener
from app.logic.dialogueDNA.events import (
    StageEvent, TranscriptionEvent, EmotionsEvent, SummaryEvent, CompletedEvent, FailedEvent, UploadEvent
)

log = logging.getLogger(__name__)

@dataclass
class PipelineSessionReporter:
    """
    Publisher that fans out pipeline events to subscribed listeners.
    - Thread-safe enough for typical usage (threaded dispatch optional).
    - Does not raise from listeners: failures are logged and ignored.
    """
    session_id: str
    dispatch: str = "sync"  # "sync" | "thread"
    _subs: List[Tuple[str, PipelineListener]] = field(default_factory=list, init=False)
    _executor: Optional[ThreadPoolExecutor] = field(default=None, init=False)

    def __init__(self, session_id: str):
        self.session_id = session_id

    def __post_init__(self):
        if self.dispatch == "thread":
            self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="pipeline-listener")

    # ------------ subscription API ------------
    def subscribe(self, listener: PipelineListener) -> str:
        token = str(uuid4())
        self._subs.append((token, listener))
        return token

    def unsubscribe(self, token: str) -> bool:
        for i, (t, _) in enumerate(self._subs):
            if t == token:
                self._subs.pop(i)
                return True
        return False

    def clear(self) -> None:
        self._subs.clear()

    # ------------ emit helpers ------------
    def stage(self, stage: str, detail: Optional[str] = None) -> None:
        self._emit("on_stage", StageEvent(self.session_id, stage, detail))

    def transcription_ready(self, transcription: TranscriptionOutput) -> None:
        self._emit("on_transcription_ready", TranscriptionEvent(self.session_id, transcription))

    def emotions_ready(self, emotions: List[EmotionAnalyzerBundle]) -> None:
        self._emit("on_emotions_ready", EmotionsEvent(self.session_id, emotions))

    def summary_ready(self, summary: SummaryOutput) -> None:
        self._emit("on_summary_ready", SummaryEvent(self.session_id, summary))

    def completed(self) -> None:
        self._emit("on_completed", CompletedEvent(self.session_id))

    def failed(self, error: str) -> None:
        self._emit("on_failed", FailedEvent(self.session_id, error))

    def file_uploaded_to_storage(self, path: str) -> None:
        self._emit("on_uploaded_to_storage", UploadEvent(self.session_id, path))

    # ------------ core dispatcher ------------
    def _emit(self, method: str, event: Any) -> None:
        for token, sub in list(self._subs):
            fn = getattr(sub, method, None)
            if not callable(fn):
                continue
            try:
                if self.dispatch == "thread" and self._executor is not None:
                    self._executor.submit(fn, event)
                else:
                    fn(event)
            except Exception as e:
                log.warning("Listener(%s) failed in %s: %s", token, method, e, exc_info=True)
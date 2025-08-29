from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from app.interfaces.services.emotions import EmotionAnalyzerBundle
from app.interfaces.services.summary import SummaryOutput
from app.interfaces.services.transcription import TranscriptionOutput


# ---- DialogueDNA milestone events ----

@dataclass(frozen=True)
class StageEvent:
    stage: str                  # e.g., "transcribing", "emotions_audio", "ready"
    detail: Optional[str] = None

@dataclass(frozen=True)
class TranscriptionEvent:
    segments: TranscriptionOutput

@dataclass(frozen=True)
class EmotionsEvent:
    emotions: List[EmotionAnalyzerBundle]

@dataclass(frozen=True)
class SummaryEvent:
    summary: SummaryOutput

@dataclass(frozen=True)
class QueuedEvent:
    pass

@dataclass(frozen=True)
class StoppedEvent:
    pass

@dataclass(frozen=True)
class ProcessingEvent:
    pass

@dataclass(frozen=True)
class FailedEvent:
    error: str


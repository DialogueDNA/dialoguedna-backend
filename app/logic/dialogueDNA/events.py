from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from app.interfaces.services.emotions import EmotionAnalyzerBundle
from app.interfaces.services.summary import SummaryOutput
from app.interfaces.services.transcription import TranscriptionOutput


# ---- pipeline milestone events ----

@dataclass(frozen=True)
class StageEvent:
    session_id: str
    stage: str                  # e.g., "transcribing", "emotions_audio", "ready"
    detail: Optional[str] = None

@dataclass(frozen=True)
class TranscriptionEvent:
    session_id: str
    segments: TranscriptionOutput

@dataclass(frozen=True)
class EmotionsEvent:
    session_id: str
    emotions: List[EmotionAnalyzerBundle]

@dataclass(frozen=True)
class SummaryEvent:
    session_id: str
    summary: SummaryOutput

@dataclass(frozen=True)
class CompletedEvent:
    session_id: str

@dataclass(frozen=True)
class FailedEvent:
    session_id: str
    error: str

@dataclass(frozen=True)
class UploadEvent:
    session_id: str
    file_path: str


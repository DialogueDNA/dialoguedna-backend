from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, List

from app.interfaces.services.audio import AudioSegment
from app.interfaces.services.text import TextSegment


@dataclass
class TranscriptionInput:
    audio:       AudioSegment
    diarization: Optional[bool] = False

TranscriptionOutput = List[TextSegment]

class Transcriber(Protocol):
    def transcribe(self, segment: TranscriptionInput) -> TranscriptionOutput: ...

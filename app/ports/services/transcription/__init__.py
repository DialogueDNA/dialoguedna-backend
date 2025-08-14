from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional

from app.ports.services.audio import AudioSegment
from app.ports.services.text import TextSegment


@dataclass
class TranscriptionSegmentInput(dict):
    """
    Input for the transcriber.
    """
    audio: AudioSegment
    diarization: Optional[bool] = False

TranscriptionSegmentOutput = TextSegment

class Transcriber(Protocol):
    def transcribe(self, segment: TranscriptionSegmentInput) -> TranscriptionSegmentOutput: ...

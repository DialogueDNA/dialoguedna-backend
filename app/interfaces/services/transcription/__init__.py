from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, List

from app.interfaces.services.audio import AudioSegment
from app.interfaces.services.text import TextSegment


@dataclass
class TranscriptionSegmentInput:
    """
    Input for the transcriber.
    """
    audio: AudioSegment
    diarization: Optional[bool] = False

TranscriptionSegmentOutput = TextSegment

class Transcriber(Protocol):
    def transcribe(self, segment: TranscriptionSegmentInput) -> List[TranscriptionSegmentOutput]: ...

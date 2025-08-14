# app/ports/transcription/transcriber.py
from __future__ import annotations
from typing import Protocol, Optional, Union

SpeakerT = Union[str, int] # e.g. "John Doe"/1

class TranscriptSegmentInput(dict):
    """
    Input for the transcriber.
    """
    audio_file_path: str
    diarization: Optional[bool] = False
    language: Optional[str]
    metadata: Optional[dict]

class TranscriptSegmentOutput(dict):
    """
    Output for the transcriber
    """
    speaker: Optional[SpeakerT]
    text: str
    start_time: Optional[float]
    end_time: Optional[float]

class Transcriber(Protocol):
    def transcribe(self, tsi: TranscriptSegmentInput) -> list[TranscriptSegmentOutput]: ...

from typing import Protocol, List, TypedDict, Dict, Optional

from app.ports.services.transcription.transcriber import TranscriptSegmentOutput, SpeakerT

TextSegmentInput = TranscriptSegmentOutput

class TextSegmentOutput(TypedDict):
    speaker: Optional[SpeakerT]
    text: str
    start_time: Optional[float]
    end_time: Optional[float]
    emotions: Dict[str, float]  # label -> score

class TextEmotionAnalyzer(Protocol):
    def analyze(self, segments: List[TextSegmentInput]) -> List[TextSegmentOutput]: ...
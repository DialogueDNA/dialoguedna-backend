from typing import Protocol, List, TypedDict, Union, Dict, Optional

from app.ports.services.emotions.audio.audio_emotion_analyzer import AudioSegmentOutput
from app.ports.services.emotions.text.text_emotion_analyzer import TextSegmentOutput

SpeakerT = Union[str, int]

class MixedSegmentOutput(TypedDict):
    speaker: Optional[SpeakerT]
    text: str
    start_time: Optional[float]
    end_time: Optional[float]
    emotions: Dict[str, float]  # label -> score

class MixedEmotionAnalyzer(Protocol):
    def fuse(self, text_results: List[TextSegmentOutput], audio_results: List[AudioSegmentOutput]) -> List[MixedSegmentOutput]: ...
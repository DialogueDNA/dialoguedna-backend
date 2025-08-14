from typing import Protocol, List, TypedDict, Union, Dict, Optional

SpeakerT = Union[str, int]

class AudioSegmentInput(TypedDict):
    speaker: Optional[SpeakerT]
    audio: str  # path to audio file or base64 encoded string
    start_time: Optional[float]
    end_time: Optional[float]

class AudioSegmentOutput(TypedDict):
    speaker: Optional[SpeakerT]
    audio: str # path to audio file or base64 encoded string
    start_time: Optional[float]
    end_time: Optional[float]
    emotions: Dict[str, float]  # label -> score

class AudioEmotionAnalyzer(Protocol):
    def analyze(self, segments: List[AudioSegmentInput]) -> List[AudioSegmentOutput]: ...
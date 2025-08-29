from dataclasses import dataclass
from typing import Optional

from app.interfaces.services import SpeakerType
from app.interfaces.services.text import TextSegment
from .type import EmotionAnalyzerOutput


@dataclass
class EmotionAnalyzerBundle:
    # All analyzers (text/audio/mixed) return EmotionAnalyzerOutput.
    text:  Optional[EmotionAnalyzerOutput] = None
    audio: Optional[EmotionAnalyzerOutput] = None
    mixed: Optional[EmotionAnalyzerOutput] = None
    whom:  Optional[SpeakerType] = None
    transcription: Optional[TextSegment] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

# Re-exports for convenience
# from .types import EmotionAnalyzerOutput, EmotionLabel, EmotionScore, EmotionsDict  # noqa: E402,F401

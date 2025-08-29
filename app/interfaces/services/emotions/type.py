from dataclasses import dataclass
from typing import Dict, Optional

from app.interfaces.services import SpeakerType

EmotionLabel = str
EmotionScore = float
EmotionsDict = Dict[EmotionLabel, EmotionScore]

@dataclass
class EmotionAnalyzerOutput:
    """Unified emotion scores payload returned by any analyzer."""
    emotions_intensity_dict: EmotionsDict
    whom: Optional[SpeakerType] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

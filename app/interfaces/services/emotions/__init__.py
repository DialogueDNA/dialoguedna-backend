from dataclasses import dataclass
from typing import Dict, Optional, List

from app.interfaces.services import SpeakerType
from app.interfaces.services.emotions.audio import EmotionAnalyzerByAudioOutput
from app.interfaces.services.emotions.mixed import EmotionAnalyzerMixerOutput
from app.interfaces.services.emotions.text import EmotionAnalyzerByTextOutput
from app.interfaces.services.text import TextSegment

EmotionLabel = str
EmotionScore = float
EmotionsDict = Dict[EmotionLabel, EmotionScore]

@dataclass
class EmotionAnalyzerOutput:
    emotions_intensity_dict:    EmotionsDict
    whom:                       Optional[SpeakerType]     = None
    start_time:                 Optional[float]           = None
    end_time:                   Optional[float]           = None

@dataclass
class EmotionAnalyzerBundle:
    text:           Optional[EmotionAnalyzerByTextOutput]     = None
    audio:          Optional[EmotionAnalyzerByAudioOutput]    = None
    mixed:          Optional[EmotionAnalyzerMixerOutput]      = None
    whom:           Optional[SpeakerType]                     = None
    transcription:  Optional[TextSegment]                     = None
    start_time:     Optional[float]                           = None
    end_time:       Optional[float]                           = None
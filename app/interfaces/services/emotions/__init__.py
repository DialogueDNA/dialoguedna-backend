from dataclasses import dataclass
from typing import Dict, Optional

EmotionLabel = str
EmotionScore = float
EmotionsDict = Dict[EmotionLabel, EmotionScore]

@dataclass
class EmotionAnalyzerOutput:
    emotions: EmotionsDict

@dataclass
class EmotionBundle:
    text: Optional[EmotionAnalyzerOutput]
    audio: Optional[EmotionAnalyzerOutput]
    mixed: Optional[EmotionAnalyzerOutput]
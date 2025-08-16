from dataclasses import dataclass
from typing import Dict

EmotionLabel = str
EmotionScore = float
EmotionsDict = Dict[EmotionLabel, EmotionScore]

@dataclass
class EmotionAnalyzerOutput:
    emotions: EmotionsDict
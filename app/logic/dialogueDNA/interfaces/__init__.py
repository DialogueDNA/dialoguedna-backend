from dataclasses import dataclass
from typing import Optional, List

from app.interfaces.services import SpeakerType
from app.interfaces.services.emotions import EmotionAnalyzerBundle
from app.interfaces.services.text import TextType
from app.interfaces.services.transcription import TranscriptionOutput

DialogueDNATranscription = TranscriptionOutput

@dataclass(frozen=True)
class DialogueDNASegmentEmotionAnalysis:
    text: TextType
    speaker: Optional[SpeakerType] = None
    start_time: Optional[float]  = None
    end_time: Optional[float]  = None
    emotion_analysis: Optional[EmotionAnalyzerBundle] = None

DialogueDNAEmotionAnalysis = List[DialogueDNASegmentEmotionAnalysis]


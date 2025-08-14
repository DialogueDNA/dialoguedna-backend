from dataclasses import dataclass

from app.core.config.services.audio import AudioUtilsConfig
from app.core.config.services.emotions import EmotionAnalysisConfig
from app.core.config.services.summary import SummarizationConfig
from app.core.config.services.transcription import TranscriptionConfig


@dataclass(frozen=True)
class ServicesConfig:
    audio_utils: AudioUtilsConfig = AudioUtilsConfig()
    transcription: TranscriptionConfig = TranscriptionConfig()
    emotion_analysis: EmotionAnalysisConfig = EmotionAnalysisConfig()
    summarization: SummarizationConfig = SummarizationConfig()
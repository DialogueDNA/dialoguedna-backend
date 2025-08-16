from dataclasses import dataclass

from app.core.config.services.emotions.audio import EmotionAudioAnalysisConfig
from app.core.config.services.emotions.mixed import EmotionMixedAnalysisConfig
from app.core.config.services.emotions.text import EmotionTextAnalysisConfig


@dataclass(frozen=True)
class EmotionAnalysisConfig:
    by_text: EmotionTextAnalysisConfig = EmotionTextAnalysisConfig()
    by_audio: EmotionAudioAnalysisConfig = EmotionAudioAnalysisConfig()
    mixed: EmotionMixedAnalysisConfig = EmotionMixedAnalysisConfig()
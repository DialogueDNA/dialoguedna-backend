from dataclasses import dataclass

from app.core.config.services.emotions.audio import AudioEmotionAnalysisConfig
from app.core.config.services.emotions.mixed import MixedEmotionAnalysisConfig
from app.core.config.services.emotions.text import TextEmotionAnalysisConfig


@dataclass(frozen=True)
class EmotionAnalysisConfig:
    by_text: TextEmotionAnalysisConfig = TextEmotionAnalysisConfig()
    by_audio: AudioEmotionAnalysisConfig = AudioEmotionAnalysisConfig()
    mixed: MixedEmotionAnalysisConfig = MixedEmotionAnalysisConfig()
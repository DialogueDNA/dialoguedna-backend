from dataclasses import dataclass
import app.core.environment as env
from app.core.config.providers.hugging_face.superb import SuperbConfig


@dataclass(frozen=True)
class EmotionAudioAnalysisConfig:
    main_analyzer: str = env.AUDIO_EMOTION_MODEL_NAME
    superb: SuperbConfig = SuperbConfig()
from dataclasses import dataclass
from app.core.config.providers.hugging_face.j_hartmann import JHartmannConfig
import app.core.environment as env

@dataclass(frozen=True)
class EmotionTextAnalysisConfig:
    main_analyzer: str = env.TEXT_EMOTION_MODEL_NAME
    j_hartmann: JHartmannConfig = JHartmannConfig()
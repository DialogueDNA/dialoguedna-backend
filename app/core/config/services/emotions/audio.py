from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class AudioEmotionAnalysisConfig:
    main_analyzer: str = env.AUDIO_EMOTION_MODEL_NAME
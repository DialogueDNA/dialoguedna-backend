from dataclasses import dataclass

from app.core.config.providers.rnnoise import RNNoiseConfig
import app.core.environment as env

@dataclass(frozen=True)
class AudioEnhancerConfig:
    main_enhancer: str = env.AUDIO_ENHANCER_MODEL_NAME
    rnnoise: RNNoiseConfig = RNNoiseConfig()
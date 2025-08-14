from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class MixedWeightConfig:
    audio_weight: float = env.FUSION_AUDIO_WEIGHT
    text_weight: float = env.FUSION_TEXT_WEIGHT
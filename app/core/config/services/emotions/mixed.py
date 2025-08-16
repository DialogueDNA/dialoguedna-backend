from dataclasses import dataclass
import app.core.environment as env
from app.services.emotions.mixed.adapters.adaptive.config import MixedAdaptiveConfig
from app.services.emotions.mixed.adapters.weights.config import MixedWeightsConfig


@dataclass(frozen=True)
class EmotionMixedAnalysisConfig:
    main_analyzer: str = env.FUSION_EMOTION_MODEL_NAME
    weights: MixedWeightsConfig = MixedWeightsConfig()
    adaptive: MixedAdaptiveConfig = MixedAdaptiveConfig()
import app.core.environment as env

from dataclasses import dataclass

@dataclass(frozen=True)
class MixedWeightsConfig:
    """
    Configuration for weighted fusion of text & audio emotion predictions.
    - text_weight + audio_weight must be > 0.
    - renorm: if True, re-normalize fused scores to sum to 1 (when sum>0).
    """
    text_weight: float = env.TEXT_WEIGHT
    audio_weight: float = env.AUDIO_WEIGHT
    renorm: bool = True

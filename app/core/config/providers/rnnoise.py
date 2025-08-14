from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class RNNoiseConfig:
    # RNNoise Enhancer Strength
    enhancer_strength: str = env.RNNOISE_ENHANCER_STRENGTH
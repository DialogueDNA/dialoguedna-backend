from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class JHartmannConfig:
    # Hugging Face Model
    model: str = env.J_HARTMANN_MODEL_NAME

    # Model Parameters
    max_length: int = 512
    truncation: bool = True
    padding: str = "max_length"

    # Device Configuration
    device: str = "cuda"
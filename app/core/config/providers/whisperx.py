from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class WhisperXConfig:
    # WhisperX Model Configuration
    model_size: str = env.WHISPERX_MODEL_SIZE
    compute_type: str = env.WHISPERX_COMPUTE_TYPE
    device: str = env.DEVICE or "cpu"
    hf_token: str = env.HUGGINGFACE_WHISPERX_TOKEN
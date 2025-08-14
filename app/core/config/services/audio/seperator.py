from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class AudioSeparationConfig:
    main_separator: str = env.AUDIO_SEPARATOR_MODEL_NAME
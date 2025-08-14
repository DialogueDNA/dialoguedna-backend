from dataclasses import dataclass
import app.core.environment as env
from app.core.config.providers.hugging_face.sepformer import SepformerConfig


@dataclass(frozen=True)
class AudioSeparatorConfig:
    main_separator: str = env.AUDIO_SEPARATOR_MODEL_NAME
    sepformer: SepformerConfig = SepformerConfig()
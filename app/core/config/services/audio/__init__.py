from dataclasses import dataclass

from app.core.config.services.audio.enhancer import AudioEnhancementConfig
from app.core.config.services.audio.seperator import AudioSeparationConfig


@dataclass(frozen=True)
class AudioUtilsConfig:
    enhancer: AudioEnhancementConfig = AudioEnhancementConfig()
    separator: AudioSeparationConfig = AudioSeparationConfig()
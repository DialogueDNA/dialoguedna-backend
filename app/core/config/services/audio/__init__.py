from dataclasses import dataclass

from app.core.config.services.audio.enhancer import AudioEnhancerConfig
from app.core.config.services.audio.seperator import AudioSeparatorConfig


@dataclass(frozen=True)
class AudioUtilsConfig:
    enhancer: AudioEnhancerConfig = AudioEnhancerConfig()
    separator: AudioSeparatorConfig = AudioSeparatorConfig()
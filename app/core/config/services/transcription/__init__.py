from dataclasses import dataclass

from app.core.config.providers.azure.speech_to_text import AzureSpeechToTextConfig
from app.core.config.providers.whisperx import WhisperXConfig
import app.core.environment as env

@dataclass(frozen=True)
class TranscriptionConfig:
    main_transcripter: str = env.TRANSCRIPTION_ADAPTER
    azure_speech_to_text: AzureSpeechToTextConfig = AzureSpeechToTextConfig()
    whisperx_model: WhisperXConfig = WhisperXConfig()
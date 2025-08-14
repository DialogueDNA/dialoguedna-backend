from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class AzureSpeechToTextConfig:
    # Azure Speech To Text Service
    key: str = env.AZURE_SPEECH_KEY
    region: str = env.AZURE_REGION

    # Optional locale for transcription
    locale: str | None = env.AZURE_SPEECH_LOCALE

    # Speaker diarization enabled by default
    speaker_diarization: bool = True
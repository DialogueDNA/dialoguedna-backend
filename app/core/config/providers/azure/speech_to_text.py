from dataclasses import dataclass
import app.core.environment as env
from typing import Optional

@dataclass(frozen=True)
class AzureSpeechToTextConfig:
    key: str = env.AZURE_SPEECH_KEY
    region: str = env.AZURE_REGION
    locale: str | None = env.AZURE_SPEECH_LOCALE
    speaker_diarization: bool = True

    use_fast_when_diarization: bool = True
    max_speakers: Optional[int] = None
from app.ports.services.transcription import Transcriber
from app.services.transcription.adapters.azure.azure_speech_transcriptor import AzureSpeechTranscriber
from app.services.transcription.plugins import register_transcriber
from app.core.config import TranscriptionConfig

@register_transcriber("azure_speech")
def build_azure_transcriber(cfg: TranscriptionConfig) -> Transcriber:
    return AzureSpeechTranscriber(key=cfg.azure_key, region=cfg.azure_region)

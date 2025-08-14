from app.core.config.services import TranscriptionConfig
from app.ports.services.transcription import Transcriber
from app.services.transcription.adapters.azure.azure_speech_to_text_transcriptor import AzureSpeechToTextTranscriber
from app.services.transcription.plugins import register_transcriber


@register_transcriber("azure_speech")
def build_azure_transcriber(cfg: TranscriptionConfig) -> Transcriber:
    return AzureSpeechToTextTranscriber(cfg.azure_speech_to_text)

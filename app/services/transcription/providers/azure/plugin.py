from app.core.config.services import TranscriptionConfig
from app.interfaces.services.transcription import Transcriber
from app.services.transcription.providers.azure.speech_to_text import AzureSpeechToTextTranscriber
from app.services.transcription.registry import register_transcriber


@register_transcriber("azure_speech_to_text")
def build_azure_transcriber(cfg: TranscriptionConfig) -> Transcriber:
    return AzureSpeechToTextTranscriber(cfg.azure_speech_to_text)

from app.core.config.services import TranscriptionConfig
from app.interfaces.services.transcription import Transcriber
from app.services.transcription.providers.whisperx.whisperx import WhisperXTranscriber
from app.services.transcription.registry import register_transcriber


@register_transcriber("whisperx")
def build_whisperx_transcriber(cfg: TranscriptionConfig) -> Transcriber:
    return WhisperXTranscriber(cfg.whisperx_model)

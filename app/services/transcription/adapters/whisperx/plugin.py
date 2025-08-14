from app.core.config.services import TranscriptionConfig
from app.ports.services.transcription import Transcriber
from app.services.transcription.adapters.whisperx.whisperx_transcriptor import WhisperXTranscriber
from app.services.transcription.plugins import register_transcriber


@register_transcriber("whisperx")
def build_whisperx_transcriber(cfg: TranscriptionConfig) -> Transcriber:
    return WhisperXTranscriber(cfg.whisperx_model)

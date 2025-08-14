from app.ports.services.transcription.transcriber import Transcriber
from app.services.transcription.adapters.whisperx.whisperx_transcriptor import WhisperXTranscriber
from app.services.transcription.plugins import register_transcriber
from app.state.app_states import TranscriptionState, StorageState
from app.core.config import TranscriptionConfig

@register_transcriber("whisperx")
def build_whisperx_transcriber(cfg: TranscriptionConfig,
                               t_state: TranscriptionState,
                               storage: StorageState) -> Transcriber:
    t = WhisperXTranscriber(
        device=cfg.device,
        model_size=cfg.whisperx_model_size,
        compute_type=cfg.whisperx_compute_type,
        hf_token=cfg.hf_token,
    )

    def transcribe_blob(container: str, blob: str, *, locale=None, speaker_diarization=True):
        if not storage.client:
            raise RuntimeError("Storage is not wired; WhisperX cannot download blob.")
        data = storage.client.download(container, blob)
        import os, tempfile
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(blob)[1] or ".wav", delete=True) as tmp:
            tmp.write(data); tmp.flush()
            return t.transcribe_file(tmp.name, locale=locale, speaker_diarization=speaker_diarization)
    setattr(t, "transcribe_blob", transcribe_blob)

    return t

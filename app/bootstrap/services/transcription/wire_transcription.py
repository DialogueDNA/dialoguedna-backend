from app.core.config.services import TranscriptionConfig
from app.services.transcription.plugins import TRANSCRIBER_PLUGINS
from app.state.app_states import TranscriptionState

def wire_transcription(transcription: TranscriptionState, transcription_cfg: TranscriptionConfig) -> None:
    if transcription is None:
        transcription = TranscriptionState()
    builder = TRANSCRIBER_PLUGINS.get(transcription_cfg.main_transcripter)
    if not builder:
        raise ValueError(f"No transcriber plugin registered for backend: {transcription_cfg.main_transcripter}")
    transcription.transcriber = builder(transcription_cfg)

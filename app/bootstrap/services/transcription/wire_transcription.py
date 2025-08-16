from __future__ import annotations
from app.core.config.services import TranscriptionConfig
from app.services.transcription.registry import build_transcriber, list_transcribers
from app.state.app_states import TranscriptionState

def wire_transcription(transcription_cfg: TranscriptionConfig) -> TranscriptionState:
    transcription = TranscriptionState()
    name = (getattr(transcription_cfg, "main_transcriber", "") or "").strip().lower()
    if not name:
        raise ValueError("TranscriptionConfig.main_transcriber is empty")

    try:
        transcription.transcriber = build_transcriber(name, transcription_cfg)
    except KeyError:
        raise ValueError(
            f"No transcriber plugin registered for: '{name}'. "
            f"Available: {', '.join(list_transcribers())}"
        )
    return transcription

from __future__ import annotations

from app.bootstrap.services.audio.wire_audio_utils import wire_audio_utils
from app.bootstrap.services.emotions.wire_emotion_analysis import wire_emotion_analysis
from app.bootstrap.services.summarization.wire_summarization import wire_summarization
from app.state.app_states import ServicesState
from app.core.config import ServicesConfig
from app.bootstrap.services.transcription.wire_transcription import wire_transcription


def wire_services(services: ServicesState, services_cfg: ServicesConfig) -> None:
    wire_audio_utils(services.audio_utils, services_cfg.audio_utils)
    wire_transcription(services.transcription, services_cfg.transcription)
    wire_emotion_analysis(services.emotion_analysis, services_cfg.emotion_analysis)
    wire_summarization(services.summarization, services_cfg.summarization)

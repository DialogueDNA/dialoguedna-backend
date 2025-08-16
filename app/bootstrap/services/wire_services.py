from __future__ import annotations

from app.bootstrap.services.audio.wire_audio_utils import wire_audio
from app.bootstrap.services.emotion_analysis.wire_emotion_analysis import wire_emotion_analysis
from app.bootstrap.services.summarization.wire_summarization import wire_summarization
from app.state.app_states import ServicesState
from app.core.config import ServicesConfig
from app.bootstrap.services.transcription.wire_transcription import wire_transcription


def wire_services(services_cfg: ServicesConfig) -> ServicesState:

    audio = wire_audio(
        enhancer_cfg=services_cfg.audio_utils.enhancer,
        separator_cfg=services_cfg.audio_utils.separator
    )

    transcription = wire_transcription(
        transcription_cfg=services_cfg.transcription
    )

    emotion_analysis = wire_emotion_analysis(
        text_cfg=services_cfg.emotion_analysis.by_text,
        audio_cfg=services_cfg.emotion_analysis.by_audio,
        mixed_cfg=services_cfg.emotion_analysis.mixed
    )

    summarization = wire_summarization(
        summarization_cfg=services_cfg.summarization
    )

    return ServicesState(audio=audio, transcription=transcription, emotion_analysis=emotion_analysis, summarization=summarization)

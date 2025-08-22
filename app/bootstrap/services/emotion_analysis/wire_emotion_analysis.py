from __future__ import annotations
from typing import Optional

from app.core.config.services.emotions import EmotionTextAnalysisConfig, EmotionAudioAnalysisConfig, \
    EmotionMixedAnalysisConfig
from app.services.emotions.audio.registry import build_emotion_audio_analyzer, list_emotion_audio_analyzer
from app.services.emotions.mixed.registry import build_emotion_mixed_analyzer, list_emotion_mixed_analyzer
from app.services.emotions.text.registry import build_emotion_text_analyzer, list_emotion_text_analyzer
from app.state.app_states import EmotionAnalysisState


def wire_emotion_analysis(
    text_cfg: EmotionTextAnalysisConfig = None,
    audio_cfg: EmotionAudioAnalysisConfig = None,
    mixed_cfg: Optional[EmotionMixedAnalysisConfig] = None,
) -> EmotionAnalysisState:
    emotions = EmotionAnalysisState()

    name = (getattr(text_cfg, "main_text_analyzer", "") or "").strip().lower()
    if not name:
        raise ValueError("EmotionTextAnalysisConfig.main_text_analyzer is empty")

    try:
        emotions.text_analyzer = build_emotion_text_analyzer(name, text_cfg)
    except KeyError:
        raise ValueError(
            f"No text emotion analyzer registered for: '{name}'. "
            f"Available: {', '.join(list_emotion_text_analyzer())}"
        )

    name = (getattr(audio_cfg, "main_audio_analyzer", "") or "").strip().lower()
    if not name:
        raise ValueError("AudioEmotionAnalysisConfig.main_audio_analyzer is empty. ")

    try:
        emotions.audio_analyzer = build_emotion_audio_analyzer(name, audio_cfg)
    except KeyError:
        raise ValueError(
            f"No audio emotion analyzer registered for: '{name}'. "
            f"Available: {', '.join(list_emotion_audio_analyzer())}"
        )

    if mixed_cfg is not None:
        name = (getattr(mixed_cfg, "main_mixer_analyzer", "") or "").strip().lower()
        if not name:
            raise ValueError("MixedEmotionConfig.main_mixer is empty")
        try:
            emotions.mixer = build_emotion_mixed_analyzer(name, mixed_cfg)
        except KeyError:
            raise ValueError(
                f"No emotion mixer registered for: '{name}'. "
                f"Available: {', '.join(list_emotion_mixed_analyzer())}"
            )

    return emotions

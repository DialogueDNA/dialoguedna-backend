from __future__ import annotations
from typing import Optional
from app.core.config.services.audio import AudioEnhancerConfig, AudioSeparatorConfig
from app.services.audio.enhance.registry import build_audio_enhancer, list_audio_enhancer
from app.services.audio.separation.registry import build_audio_separator, list_audio_separator
from app.state.app_states import AudioState

def wire_audio(
    enhancer_cfg: Optional[AudioEnhancerConfig] = None,
    separator_cfg: Optional[AudioSeparatorConfig] = None,
) -> AudioState:
    audio = AudioState()

    if enhancer_cfg is not None:
        name = (getattr(enhancer_cfg, "main_enhancer", "") or "").strip().lower()
        if not name:
            raise ValueError("AudioEnhancerConfig.main_enhancer is empty")
        try:
            audio.enhancer = build_audio_enhancer(name, enhancer_cfg)
        except KeyError:
            raise ValueError(
                f"No audio enhancer plugin registered for: '{name}'. "
                f"Available: {', '.join(list_audio_enhancer())}"
            )

    if separator_cfg is not None:
        name = (getattr(separator_cfg, "main_separator", "") or "").strip().lower()
        if not name:
            raise ValueError("AudioSeparatorConfig.main_separator is empty")
        try:
            audio.separator = build_audio_separator(name, separator_cfg)
        except KeyError:
            raise ValueError(
                f"No audio separator plugin registered for: '{name}'. "
                f"Available: {', '.join(list_audio_separator())}"
            )

    return audio

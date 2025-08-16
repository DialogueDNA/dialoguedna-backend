from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config.services.emotions import EmotionAudioAnalysisConfig
from app.interfaces.services.emotions.audio import EmotionAudioAnalyzer

# Typed registry for emotion audio analyzers
emotion_audio_analyzer_registry: PluginRegistry[EmotionAudioAnalysisConfig, EmotionAudioAnalyzer] = PluginRegistry()

# Public API
register_emotion_audio_analyzer = emotion_audio_analyzer_registry.register
build_emotion_audio_analyzer    = emotion_audio_analyzer_registry.create
get_emotion_audio_analyzer      = emotion_audio_analyzer_registry.get
list_emotion_audio_analyzer     = emotion_audio_analyzer_registry.names

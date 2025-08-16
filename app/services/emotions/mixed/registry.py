from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config.services.emotions import EmotionMixedAnalysisConfig
from app.interfaces.services.emotions.mixed import EmotionMixedAnalyzer

# Typed registry for emotion mixed analyzers
emotion_mixed_analyzer_registry: PluginRegistry[EmotionMixedAnalysisConfig, EmotionMixedAnalyzer] = PluginRegistry()

# Public API
register_emotion_mixed_analyzer = emotion_mixed_analyzer_registry.register
build_emotion_mixed_analyzer    = emotion_mixed_analyzer_registry.create
get_emotion_mixed_analyzer      = emotion_mixed_analyzer_registry.get
list_emotion_mixed_analyzer     = emotion_mixed_analyzer_registry.names

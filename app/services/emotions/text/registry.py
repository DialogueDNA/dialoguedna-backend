from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config.services.emotions import EmotionTextAnalysisConfig
from app.interfaces.services.emotions.text import EmotionTextAnalyzer

# Typed registry for emotion text analyzers
emotion_text_analyzer_registry: PluginRegistry[EmotionTextAnalysisConfig, EmotionTextAnalyzer] = PluginRegistry()

# Public API
register_emotion_text_analyzer = emotion_text_analyzer_registry.register
build_emotion_text_analyzer    = emotion_text_analyzer_registry.create
get_emotion_text_analyzer      = emotion_text_analyzer_registry.get
list_emotion_text_analyzer     = emotion_text_analyzer_registry.names

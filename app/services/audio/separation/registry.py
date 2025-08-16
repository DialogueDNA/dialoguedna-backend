from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config.services.audio import AudioSeparatorConfig
from app.interfaces.services.audio.separator import AudioSeparator

# Typed registry for audio separators
audio_separator_registry: PluginRegistry[AudioSeparatorConfig, AudioSeparator] = PluginRegistry()

# Public API
register_audio_separator = audio_separator_registry.register
build_audio_separator    = audio_separator_registry.create
get_audio_separator      = audio_separator_registry.get
list_audio_separator     = audio_separator_registry.names

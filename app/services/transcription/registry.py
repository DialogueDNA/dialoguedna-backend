from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config.services import TranscriptionConfig
from app.interfaces.services.transcription import Transcriber

# Typed registry for transcribers
transcriber_registry: PluginRegistry[TranscriptionConfig, Transcriber] = PluginRegistry()

# Public API
register_transcriber = transcriber_registry.register
build_transcriber    = transcriber_registry.create
get_transcriber      = transcriber_registry.get
list_transcribers    = transcriber_registry.names

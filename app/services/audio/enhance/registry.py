from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config.services.audio import AudioEnhancerConfig
from app.interfaces.services.audio.enhancer import AudioEnhancer

# Typed registry for audio enhancers
audio_enhancer_registry: PluginRegistry[AudioEnhancerConfig, AudioEnhancer] = PluginRegistry()

# Public API
register_audio_enhancer = audio_enhancer_registry.register
build_audio_enhancer    = audio_enhancer_registry.create
get_audio_enhancer      = audio_enhancer_registry.get
list_audio_enhancer     = audio_enhancer_registry.names

from __future__ import annotations
from app.common.plugin_registry import PluginRegistry
from app.core.config.services import SummarizationConfig
from app.interfaces.services.summary import Summarizer

# Typed registry for summarizers
summary_registry: PluginRegistry[SummarizationConfig, Summarizer] = PluginRegistry()

# Public API
register_summarizer = summary_registry.register
build_summarizer    = summary_registry.create
get_summarizer      = summary_registry.get
list_summarizers    = summary_registry.names

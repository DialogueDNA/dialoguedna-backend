from __future__ import annotations
from typing import Callable, Dict

from app.core.config.services import SummarizationConfig
from app.ports.services.summary import Summarizer

SummarizerPlugin = Callable[[SummarizationConfig], Summarizer]
SUMMARIZER_PLUGINS: Dict[str, SummarizerPlugin] = {}

def register_summarizer(name: str):
    """
    Decorator to register a summarizer builder under a unique name.
    Example: @register_summarizer("azure-openai")
    """
    def deco(fn: SummarizerPlugin):
        SUMMARIZER_PLUGINS[name] = fn
        return fn
    return deco

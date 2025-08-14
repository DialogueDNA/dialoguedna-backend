from __future__ import annotations
from typing import Callable, Dict

from app.core.config.services import TranscriptionConfig
from app.ports.services.transcription import Transcriber

TranscriberPlugin = Callable[[TranscriptionConfig], Transcriber]
TRANSCRIBER_PLUGINS: Dict[str, TranscriberPlugin] = {}

def register_transcriber(backend: str):
    def deco(fn: TranscriberPlugin):
        TRANSCRIBER_PLUGINS[backend] = fn
        return fn
    return deco

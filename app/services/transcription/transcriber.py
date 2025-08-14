"""
Generic Transcriber facade using the Strategy pattern.
- Plug in AzureSpeechTranscriber or WhisperXTranscriber interchangeably.
- Keeps a tiny interface: transcribe(audio_path) -> list[dict].
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseTranscriber(Protocol):
    def transcribe(self, audio_path: str) -> list[dict[str, Any]]: ...


class Transcriber:
    """Thin facade that delegates to a concrete transcriber strategy."""

    def __init__(self, strategy: BaseTranscriber) -> None:
        if not isinstance(strategy, BaseTranscriber):
            raise TypeError("strategy must implement BaseTranscriber Protocol")
        self._strategy = strategy

    def transcribe(self, audio_path: str) -> list[dict[str, Any]]:
        return self._strategy.transcribe(audio_path)

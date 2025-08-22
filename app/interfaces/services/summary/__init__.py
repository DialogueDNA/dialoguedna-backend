from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Dict, Optional

from app.interfaces.services import SpeakerType
from app.interfaces.services.emotions import EmotionAnalyzerOutput, EmotionBundle
from app.interfaces.services.text import TextType

@dataclass(frozen=True)
class SummarySegment:
    """Summarizer input segment contract."""
    text: TextType                               # text to summarize
    speaker: Optional[SpeakerType] = None
    start_time: Optional[float]  = None
    end_time: Optional[float]  = None
    emotion_analysis: Optional[EmotionBundle] = None

Segments = List[SummarySegment]

@dataclass
class SummaryInput:
    """Summarizer input contract."""
    segments: Segments
    style: str                                  # key from prompts.PROMPT_PRESETS, e.g. "ALL_IN_ONE"
    max_tokens: Optional[int] = None            # optional max tokens for the summary
    language: Optional[str] = None              # optional forced output language
    per_speaker: Optional[bool] = None
    bullets: Optional[bool] = None
    metadata: Optional[Dict[str, str]] = None   # optional arbitrary metadata for prompt conditioning

@dataclass
class SummaryOutput:
    """Summarizer output contract."""
    summary: str
    per_speaker: Optional[Dict[str, str]]  # optional per-speaker mini-summaries
    bullets: Optional[List[str]]           # optional bullets, if adapter returns them
    usage: Optional[Dict[str, float]]      # tokens/latency/etc.

class Summarizer(Protocol):
    """Strategy interface for any summarizer backend."""
    def summarize(self, req: SummaryInput) -> SummaryOutput: ...

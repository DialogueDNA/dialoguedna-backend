from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Dict, Optional

from app.ports.services.emotions import EmotionAnalyzerOutput

SummarySegment = EmotionAnalyzerOutput

@dataclass
class SummaryInput:
    """Summarizer input contract."""
    segments: List[SummarySegment]
    style: str                           # key from prompts.PROMPT_PRESETS, e.g. "ALL_IN_ONE"
    max_tokens: Optional[int]            # optional max tokens for the summary
    language: Optional[str]              # optional forced output language
    metadata: Optional[Dict[str, str]]   # optional arbitrary metadata for prompt conditioning

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

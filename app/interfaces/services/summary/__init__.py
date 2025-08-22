from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, List, Dict, Optional

from app.interfaces.services import SpeakerType
from app.interfaces.services.emotions import EmotionAnalyzerBundle
from app.interfaces.services.text import TextType

@dataclass
class SummaryInput:
    segments:       List[EmotionAnalyzerBundle]
    style:          str                                         # key from prompts.PROMPT_PRESETS, e.g. "ALL_IN_ONE"
    max_tokens:     Optional[int]             = None            # optional max tokens for the summary
    language:       Optional[str]             = None            # optional forced output language
    per_speaker:    Optional[bool]            = None
    bullets:        Optional[bool]            = None
    metadata:       Optional[Dict[str, str]]  = None            # optional arbitrary metadata for prompt conditioning

@dataclass
class SummaryOutput:
    summary:        str
    per_speaker:    Optional[Dict[str, str]]   = None           # optional per-speaker mini-summaries
    bullets:        Optional[List[str]]        = None           # optional bullets, if adapter returns them
    usage:          Optional[Dict[str, float]] = None           # tokens/latency/etc.

class Summarizer(Protocol):
    def summarize(self, req: SummaryInput) -> SummaryOutput: ...

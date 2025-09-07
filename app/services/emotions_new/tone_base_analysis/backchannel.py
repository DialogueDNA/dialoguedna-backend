# Path: app/services/emotions_new/tone_base_analysis/backchannel.py
# Purpose: Detect backchannel/very short acknowledgments.
from __future__ import annotations

from typing import Iterable

PHRASE_MAX_SEC = 1.0
VERY_SHORT_SEC = 0.7

BACKCHANNEL_PHRASES: tuple[str, ...] = (
    "go on",
    "ok",
    "okay",
    "uh-huh",
    "mm",
    "yes",
    "yeah",
    "right",
    "sure",
)

def _contains_phrase(text: str, phrases: Iterable[str]) -> bool:
    t = text.strip().lower()
    return any(p in t for p in phrases)

def detect(text: str, duration_sec: float) -> bool:
    duration_sec = float(duration_sec)
    if duration_sec <= PHRASE_MAX_SEC and _contains_phrase(text, BACKCHANNEL_PHRASES):
        return True
    if duration_sec < VERY_SHORT_SEC and len(text.strip()) <= 3:
        return True
    return False

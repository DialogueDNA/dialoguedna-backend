from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from transformers import pipeline

from app.core.config import TEXT_EMOTION_MODEL, TOP_K_EMOTIONS


@dataclass
class TextEmotionResult:
    emotions_intensity_dict: Dict[str, float]
    text: str
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class TextEmotionAnalyzer:
    """
    Wraps a HF text-classification pipeline to produce label->score distributions
    per transcript entry.
    """

    def __init__(self) -> None:
        self._clf = pipeline(
            "text-classification",
            model=TEXT_EMOTION_MODEL,
            top_k=TOP_K_EMOTIONS,
            return_all_scores=True if (TOP_K_EMOTIONS is None or str(TOP_K_EMOTIONS).strip() in ("", "0", "None")) else False,
        )

    def analyze_single(self, *, text: str) -> Dict[str, float]:
        t = (text or "").strip()
        if not t:
            return {}

        raw = self._clf(t)
        items: List[Dict[str, Any]]
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            items = [raw[0]]
        elif isinstance(raw, list) and raw and isinstance(raw[0], list):
            items = list(raw[0])
        else:
            items = []
        return {it["label"]: float(it["score"]) for it in items}

    def analyze_transcript(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        results: List[Dict[str, float]] = []
        for entry in transcript:
            results.append(self.analyze_single(text=str(entry.get("text", ""))))
        return results



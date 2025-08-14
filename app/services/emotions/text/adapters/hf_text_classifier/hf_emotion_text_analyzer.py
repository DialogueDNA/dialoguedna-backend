from __future__ import annotations
import os
from typing import Dict, Any, List

from transformers import pipeline

from app.core.config.providers.hugging_face.j_hartmann import JHartmannConfig
from app.ports.services.emotions import EmotionAnalyzerOutput
from app.ports.services.emotions.text_analyzer import (
    TextEmotionAnalyzer,
    EmotionAnalyzerByTextInput,
    EmotionAnalyzerByTextOutput,
)

class HFTextClassifier(TextEmotionAnalyzer):
    """
    Hugging Face sequence classifier for text-based emotion inference.

    Contract:
      - __init__(cfg: JHartmannConfig)
      - analyze_text(segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput

    Input:
      - segment.text: str (required; empty/whitespace yields empty emotions)
      - segment.language / writer / start_time / end_time are ignored here, but kept
        on the segment for pipeline compatibility elsewhere.

    Output:
      - EmotionAnalyzerOutput(emotions: Dict[str, float])
    """

    def __init__(self, cfg: JHartmannConfig):
        self._cfg = cfg
        os.makedirs(cfg.cache_dir, exist_ok=True)
        # Build a HF pipeline. If top_k is None we ask for all scores.
        self._clf = pipeline(
            task="text-classification",
            model=cfg.model,
            device=cfg.device,
            return_all_scores=True if cfg.top_k is None else False,
            top_k=cfg.top_k,
            model_kwargs={"cache_dir": cfg.cache_dir},
        )

    def analyze_text(self, segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput:
        text = (segment.text or "").strip()
        if not text:
            return EmotionAnalyzerOutput(emotions={})

        # HF pipeline returns (for single string):
        # - top_k=None, return_all_scores=True: [ [ {label, score}, ... ] ]
        # - top_k=K:                           [ [ {label, score} x K ] ]
        # - top_k default (=1):                [ {label, score} ]
        raw = self._clf(text)

        # Normalize outputs to a flat list of {label, score}
        items: List[Dict[str, Any]]
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            # case: [ {label, score} ]
            items = [raw[0]]
        elif isinstance(raw, list) and raw and isinstance(raw[0], list):
            # case: [ [ ... ] ]
            items = list(raw[0])
        else:
            items = []

        emotions = {it["label"]: float(it["score"]) for it in items}
        return EmotionAnalyzerOutput(emotions=emotions)

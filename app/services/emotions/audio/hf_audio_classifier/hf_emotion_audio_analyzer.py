from __future__ import annotations
from typing import Dict, Any, List

from transformers import pipeline

from app.core.config.providers.hugging_face.j_hartmann import JHartmannConfig
from app.ports.services.emotions import EmotionAnalyzerOutput
from app.ports.services.emotions.text_analyzer import (
    TextEmotionAnalyzer,
    EmotionAnalyzerByTextInput,
    EmotionAnalyzerByTextOutput,
)

class JHartmannTextEmotionAnalyzer(TextEmotionAnalyzer):
    """
    Text emotion analyzer backed by the Hugging Face pipeline.

    Behavior matches the example you provided:
      classifier = pipeline("text-classification",
                            model="j-hartmann/emotion-english-distilroberta-base",
                            return_all_scores=True)
      classifier("I love this!") -> [[{label, score}, ...]]

    API:
      - __init__(cfg: JHartmannConfig)
      - analyze_text(segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput
    """

    def __init__(self, cfg: JHartmannConfig):
        self._cfg = cfg
        # Build a pipeline once; always ask for all scores to mirror the example.
        self._clf = pipeline(
            task="text-classification",
            model=cfg.model,
            device=cfg.device,
            return_all_scores=True,
            model_kwargs={"cache_dir": cfg.cache_dir},
        )

    def analyze_text(self, segment: EmotionAnalyzerByTextInput) -> EmotionAnalyzerByTextOutput:
        """
        Accepts a single TextSegment and returns EmotionAnalyzerOutput.
        Only `segment.text` is used here (writer/timestamps/language are ignored).
        """
        text = (segment.text or "").strip()
        if not text:
            return EmotionAnalyzerOutput(emotions={})

        raw: Any = self._clf(text)
        # Normalize HF outputs into a flat list[{label, score}]
        # Examples:
        #  - return_all_scores=True: [ [ {label, score}, ... ] ]
        #  - occasionally:           [ {label, score}, ... ]
        items: List[Dict[str, Any]] = []
        if isinstance(raw, list) and raw:
            first = raw[0]
            if isinstance(first, list):
                # [[{label, score}, ...]]
                items = [it for it in first if isinstance(it, dict)]
            elif isinstance(first, dict):
                # [{label, score}, ...]
                items = [it for it in raw if isinstance(it, dict)]

        emotions = {it["label"]: float(it["score"]) for it in items if "label" in it and "score" in it}
        return EmotionAnalyzerOutput(emotions=emotions)

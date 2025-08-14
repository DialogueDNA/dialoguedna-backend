from __future__ import annotations
from typing import List
from transformers import pipeline

from app.ports.services.emotions.text_emotioner import TextSegmentInput, TextSegmentOutput, TextEmotionAnalyzer


class HFTextClassifier(TextEmotionAnalyzer):
    """
    Hugging Face sequence classifier for text-based emotion inference.
    Conforms to TextEmotionAnalyzer (analyze_text(...)).
    """
    def __init__(self, model_name: str, top_k: int | None = None):
        self._clf = pipeline(
            "text-classification",
            model=model_name,
            return_all_scores=True if top_k is None else False,
            top_k=top_k
        )

    def analyze_text(self, segments: List[TextSegmentInput]) -> List[TextSegmentOutput]:
        outputs: List[TextSegmentOutput] = []
        for seg in segments:
            text = seg.get("text", "")
            if not text.strip():
                outputs.append({
                    "speaker": seg.get("speaker", "?"),
                    "text": text,
                    "start_time": float(seg.get("start_time", 0.0)),
                    "end_time": float(seg.get("end_time", 0.0)),
                    "emotions": {}
                })
                continue
            pred = self._clf(text)[0]
            if isinstance(pred, dict):  # top_k=1
                emotions = {pred["label"]: float(pred["score"])}
            else:
                emotions = {p["label"]: float(p["score"]) for p in pred}
            outputs.append({
                "speaker": seg.get("speaker", "?"),
                "text": text,
                "start_time": float(seg.get("start_time", 0.0)),
                "end_time": float(seg.get("end_time", 0.0)),
                "emotions": emotions
            })
        return outputs

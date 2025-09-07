# app/services/emotions/text_base_analysis/text_base_analyzer.py
# Text-based emotion analysis using a Hugging Face classifier (outputs 7-class probabilities per utterance).

from typing import Any, Dict, List
from transformers import pipeline
from app.core.config import TEXT_EMOTION_MODEL, TOP_K_EMOTIONS,EMOTIONS_7

class TextBaseAnalyzer:
    def __init__(self) -> None:
        top_k = TOP_K_EMOTIONS or 6
        self.classifier = pipeline(
            "text-classification",
            model=TEXT_EMOTION_MODEL,
            top_k=top_k,
            return_all_scores=True,
            truncation=True,
        )

    def analyze(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        for entry in transcript:
            speaker = str(entry.get("speaker", "?")).strip()
            text = str(entry.get("text", "")).strip()
            start_sec = float(entry.get("start_time", 0.0))
            end_sec = float(entry.get("end_time", start_sec))

            if not text:
                emotions = [{"label": lbl, "score": 1.0 / len(EMOTIONS_7)} for lbl in EMOTIONS_7]
            else:
                out = self.classifier(text)
                items = out[0] if isinstance(out, list) and out and isinstance(out[0], list) else out
                by_label = {str(it["label"]).lower(): float(it["score"]) for it in items}
                emotions = [{"label": lbl, "score": float(by_label.get(lbl, 0.0))} for lbl in EMOTIONS_7]
                emotions.sort(key=lambda x: x["score"], reverse=True)

            results.append({
                "speaker": speaker,
                "text": text,
                "start_time": start_sec,
                "end_time": end_sec,
                "emotions": emotions,
            })

        return results

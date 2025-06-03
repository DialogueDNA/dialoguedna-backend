from typing import Any
from collections import defaultdict
from transformers import pipeline

from app.core.config import TEXT_EMOTION_MODEL, TOP_K_EMOTIONS

class Emotioner:
    def __init__(self):
        self.overall_emotions = None
        self.speaker_emotions = None

    def get_emotions(self, transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
        print("🔍 Running text-based emotion analysis...")

        classifier = pipeline("text-classification", model=TEXT_EMOTION_MODEL, top_k=TOP_K_EMOTIONS)

        results = []

        self.speaker_emotions = defaultdict(lambda: defaultdict(float))
        self.overall_emotions = defaultdict(float)

        for entry in transcript:
            speaker = str(entry.get("speaker", "?")).strip()
            text = entry.get("text", "").strip()

            if not text:
                continue

            start_sec = entry.get("start_time", 0)
            end_sec = entry.get("end_time", 0)

            emotions = classifier(text)

            result_entry = {
                "speaker": speaker,
                "text": text,
                "start_time": start_sec,
                "end_time": end_sec,
                "emotions": emotions[0],
            }
            results.append(result_entry)

        return results
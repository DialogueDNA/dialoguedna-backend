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
        output_txt = ""

        self.speaker_emotions = defaultdict(lambda: defaultdict(float))
        self.overall_emotions = defaultdict(float)

        for entry in transcript:
            speaker = str(entry.get("speaker", "?")).strip()
            text = entry.get("text", "").strip()

            if not text:
                continue

            emotions = classifier(text)

            result_entry = {
                "speaker": speaker,
                "text": text,
                "emotions": emotions
            }
            results.append(result_entry)

            # output_txt += f"{speaker}: {text}\n"
            # for e in emotions[0]:
            #     label = e['label'].lower()
            #     score = round(e['score'] * 100, 2)
            #     output_txt += f"  {label}: {score}%\n"
            #     self.speaker_emotions[speaker][label] += score
            #     self.overall_emotions[label] += score
            # output_txt += "\n"
        print("Emotion analysis completed.", results)
        return results

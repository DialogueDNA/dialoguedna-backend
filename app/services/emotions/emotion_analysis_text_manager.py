# File: emotion_analysis_text_manager.py

import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from transformers import pipeline

from app.core.config import TEXT_EMOTION_MODEL, TOP_K_EMOTIONS


class EmotionAnalysisTextManager:
    def __init__(self, transcript: str, output_dir: Path, session_id: str):
        self.transcript = transcript
        self.output_dir = output_dir / session_id  # Session-specific folder
        self.session_id = session_id
        self.speaker_emotions = defaultdict(lambda: defaultdict(float))
        self.overall_emotions = defaultdict(float)

    def analyze(self) -> str:
        print("🔍 Running text-based emotion analysis...")

        # Load pre-trained emotion classification pipeline
        classifier = pipeline("text-classification", model=TEXT_EMOTION_MODEL, top_k=TOP_K_EMOTIONS)

        # Split the transcript into lines
        lines = self.transcript.strip().splitlines()

        results = []
        output_txt = ""

        for line in lines:
            if not line.strip():
                continue

            try:
                speaker, text = line.split(":", 1)
            except ValueError:
                continue  # Skip malformed lines

            emotions = classifier(text.strip())

            result_entry = {
                "speaker": speaker.strip(),
                "text": text.strip(),
                "emotions": emotions
            }
            results.append(result_entry)

            output_txt += f"{speaker.strip()}: {text.strip()}\n"
            for e in emotions[0]:
                output_txt += f"  {e['label'].lower()}: {round(e['score'] * 100, 2)}%\n"
                self.speaker_emotions[speaker.strip()][e['label'].lower()] += round(e['score'] * 100, 2)
                self.overall_emotions[e['label'].lower()] += round(e['score'] * 100, 2)
            output_txt += "\n"

        # Create output folder for this session
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write detailed output
        txt_path = self.output_dir / "text_emotions.txt"
        json_path = self.output_dir / "text_emotions.json"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(output_txt)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Save summary statistics
        self._save_json_summary()
        self._save_txt_summary()

        return txt_path  # or return both paths if needed

    def _save_json_summary(self):
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall": dict(self.overall_emotions),
            "per_speaker": {k: dict(v) for k, v in self.speaker_emotions.items()}
        }
        with open(self.output_dir / "emotion_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    def _save_txt_summary(self):
        path = self.output_dir / "emotion_summary.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("📊 Overall Emotions:\n")
            for emotion, score in self.overall_emotions.items():
                f.write(f"- {emotion}: {score:.2f}%\n")
            f.write("\n")

            for speaker, emotions in self.speaker_emotions.items():
                f.write(f"👤 {speaker}:\n")
                for emotion, score in emotions.items():
                    f.write(f"  - {emotion}: {score:.2f}%\n")
                f.write("\n")

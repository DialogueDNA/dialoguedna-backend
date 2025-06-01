from typing import List, Dict
from app.services.summarizer_engine import SummarizerEngine
from app.core.config import SUMMARY_DIR
import requests
import tempfile
import json

class Summarizer:
    def __init__(self):
        self.engine = SummarizerEngine(output_dir=SUMMARY_DIR)

    def _load_emotions_from_sas_url(self, sas_url: str) -> Dict[str, List[Dict]]:
        """Download emotion JSON file and parse as structured speaker-emotion data"""
        response = requests.get(sas_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download emotion JSON: {response.status_code}")

        data = response.json()

        # Build: {speaker: [{text, emotions}]}
        result = {}
        for entry in data:
            speaker = entry["speaker"]
            if speaker not in result:
                result[speaker] = []
            result[speaker].append({
                "text": entry["text"],
                "emotions": entry["emotions"]
            })
        return result

    def generate(self, emotion_json_url: str, speakers: List[str]) -> Dict[str, str]:
        emotions = self._load_emotions_from_sas_url(emotion_json_url)

        annotated = []
        for speaker in speakers:
            for item in emotions.get(speaker, []):
                annotated.append({
                    "speaker": speaker,
                    "text": item["text"],
                    "emotions": item.get("emotions", [])
                })

        summary_text = self.engine.summarize(annotated)
        return {"summary": summary_text}

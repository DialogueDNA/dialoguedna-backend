from typing import List, Dict
from app.services.summarizer_engine import SummarizerEngine
from app.services.azure_uploader import AzureUploader
from app.core.config import SUMMARY_DIR, AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
import requests
import json
from pathlib import Path

class Summarizer:
    def __init__(self):
        self.engine = SummarizerEngine(output_dir=SUMMARY_DIR)
        self.uploader = AzureUploader(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )

    def _load_emotions_from_sas_url(self, sas_url: str) -> Dict[str, List[Dict]]:
        response = requests.get(sas_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download emotion JSON: {response.status_code}")
        data = response.json()

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

    def generate(self, emotion_json_url: str, speakers: List[str], session_id: str) -> str:
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

        # ✨ שמירה לקובץ מקומי
        output_dir = SUMMARY_DIR / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "conversation_summary.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_text)

        # ☁️ העלאה ל-Azure
        blob_name = f"{session_id}/conversation_summary.md"
        sas_url = self.uploader.upload_file_and_get_sas(summary_path, blob_name=blob_name)

        print("✅ Summary uploaded successfully.")
        return sas_url

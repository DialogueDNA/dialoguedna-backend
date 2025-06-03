# summarizer.py

from typing import List, Dict
from app.services.summarization.summarizer_engine import SummarizerEngine
from app.services.infrastructure.azure_uploader import AzureUploader
from app.core.config import SUMMARY_DIR, AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
import json
from pathlib import Path
from pprint import pprint

class Summarizer:
    def __init__(self):
        self.engine = SummarizerEngine()
        self.uploader = AzureUploader(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )

    def generate(self, emotions_bundle: Dict, session_id: str) -> str:
        emotions = emotions_bundle["emotions_dict"]
        print("🎙 Emotions dictionary:")
        pprint(emotions)

        annotated = []
        for speaker, utterances in emotions.items():
            for item in utterances:
                annotated.append({
                    "speaker": speaker,
                    "text": item["text"],
                    "emotions": item["emotions"][0]  # נשלפת הרשימה הפנימית
                })

        print("📊 Annotated input:")
        pprint(annotated)
        summary_text = self.engine.summarize(annotated)

        output_dir = SUMMARY_DIR / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "conversation_summary.md"

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_text)

        blob_name = f"{session_id}/conversation_summary.md"
        sas_url = self.uploader.upload_file_and_get_sas(summary_path, blob_name=blob_name)

        print("✅ Summary uploaded successfully.")
        return sas_url

    # def _load_emotions_from_sas_url(self, sas_url: str) -> Dict[str, List[Dict]]:
    #     # response = requests.get(sas_url)
    #     # if response.status_code != 200:
    #     #     raise Exception(f"Failed to download emotion JSON: {response.status_code}")
    #     # data = response.json()
    #
    #     json_path = Path(
    #         r"/app/conversation_session/session_2025-06-01_00-28-42/processed/transcript_emotion_text/0e139d18-0266-4be1-b569-c46b34c9af82/text_emotions.json"
    #     )
    #
    #     print("📂 Trying to load:", json_path)
    #
    #     with open(json_path, "r", encoding="utf-8") as f:
    #         data = json.load(f)
    #
    #     result = {}
    #     for entry in data:
    #         speaker = entry["speaker"]
    #         if speaker not in result:
    #             result[speaker] = []
    #         result[speaker].append({
    #             "text": entry["text"],
    #             "emotions": entry["emotions"]
    #         })
    #     return result
    #
    # def generate(self, emotion_json_url: str, speakers: List[str], session_id: str) -> str:
    #     emotions = self._load_emotions_from_sas_url(emotion_json_url)
    #     print("🎙 Emotions dictionary:")
    #     pprint(emotions)
    #
    #     annotated = []
    #     for speaker, utterances in emotions.items():
    #         for item in utterances:
    #             annotated.append({
    #                 "speaker": speaker,
    #                 "text": item["text"],
    #                 "emotions": item["emotions"][0]  # נשלפת הרשימה הפנימית
    #             })
    #
    #     print("📊 Annotated input:")
    #     pprint(annotated)
    #     summary_text = self.engine.summarize(annotated)
    #
    #     output_dir = SUMMARY_DIR / session_id
    #     output_dir.mkdir(parents=True, exist_ok=True)
    #     summary_path = output_dir / "conversation_summary.md"
    #     with open(summary_path, "w", encoding="utf-8") as f:
    #         f.write(summary_text)
    #
    #     blob_name = f"{session_id}/conversation_summary.md"
    #     sas_url = self.uploader.upload_file_and_get_sas(summary_path, blob_name=blob_name)
    #
    #     print("✅ Summary uploaded successfully.")
    #     return sas_url

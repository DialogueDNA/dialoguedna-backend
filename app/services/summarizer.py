"""
summarizer.py

Summarizer service – wraps SummarizerEngine to generate emotional summaries.

Responsibilities:
- Accept transcription text, emotion data, and speaker list
- Flatten the data into a sentence-level annotated list
- Delegate summarization to SummarizerEngine (Azure OpenAI)
- Return the summary text
"""

from typing import List, Dict
from app.services.summarizer_engine import SummarizerEngine
from app.core.config import SUMMARY_DIR

class Summarizer:
    def __init__(self):
        self.engine = SummarizerEngine(output_dir=SUMMARY_DIR)

    def generate(self, text: str, emotions: Dict[str, List[Dict]], speakers: List[str]) -> Dict[str, str]:
        """
        Generate a single summary based on all speakers' emotional content.

        :param text: Transcribed text (not used directly here)
        :param emotions: Per-speaker emotion data
        :param speakers: List of speaker IDs
        :return: Dictionary with final summary
        """
        # Flatten speaker -> list into single annotated sentence list
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

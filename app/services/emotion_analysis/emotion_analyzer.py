"""
emotion_analyzer.py

EmotionAnalyzer service – wraps EmotionTextEngine to provide API-ready structure.

Responsibilities:
- Accept audio path and diarized text segments
- Delegate emotion detection to EmotionTextEngine
- Return results in speaker-wise structured format
"""

from typing import List, Dict
from pathlib import Path
from app.services.emotion_analysis.emotion_text_engine import EmotionTextEngine
from app.core.config import EMOTIONS_TEXT_DIR
from app.services.utils import save_json

class EmotionAnalyzer:
    def __init__(self):
        self.engine = EmotionTextEngine()

    def analyze(self, audio_path: str, segments: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Perform emotion analysis on diarized transcript.

        :param audio_path: Path to original audio file (used for naming outputs)
        :param segments: List of {"speaker": str, "text": str}
        :return: Dict of per-speaker emotion data
        """
        speaker_emotions = self.engine.analyze_segments(segments)

        # Optional: Save output to JSON
        save_path = EMOTIONS_TEXT_DIR / (Path(audio_path).stem + "_text_emotions.json")
        save_json(speaker_emotions, save_path)

        return speaker_emotions

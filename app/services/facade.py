"""
facade.py

This module defines the DialogueProcessor facade class.

Responsibilities:
- Coordinate the entire analysis pipeline from audio input to structured output.
- Delegate tasks to specialized services:
    - Transcriber (speech-to-text)
    - Diarizer (speaker diarization)
    - EmotionAnalyzer (voice-based emotion recognition)
    - Summarizer (emotional summary + insights)
- Return a structured result to the API.
"""

from app.services.transcriber import Transcriber
from app.services.diarizer import Diarizer
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.summarizer import Summarizer

class DialogueProcessor:
    def __init__(self):
        self.transcriber = Transcriber()
        self.diarizer = Diarizer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.summarizer = Summarizer()

    def process_audio(self, audio_path: str) -> dict:
        """
        Process an audio file and return analysis results.

        :param audio_path: Path to the uploaded audio file
        :return: Dictionary with transcription, speaker info, emotions, and summary
        """
        text = self.transcriber.transcribe(audio_path)
        speaker_segments = self.diarizer.identify(audio_path)
        emotions = self.emotion_analyzer.analyze(audio_path, speaker_segments)
        speaker_ids = list(emotions.keys())
        summary = self.summarizer.generate(text, emotions, speaker_ids)

        return {
            "transcription": text,
            "speakers": speaker_segments,
            "emotions": emotions,
            "summary": summary
        }

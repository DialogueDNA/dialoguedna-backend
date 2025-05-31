from typing import Optional

from fastapi import UploadFile

from app.services.db_loader import DBLoader
from app.services.diarizer import Diarizer
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.sessionDB import SessionDB
from app.services.summarizer import Summarizer
from app.services.transcriber import Transcriber


class DialogueProcessor:
    def __init__(self):
        self.DBLoader = DBLoader()
        self.session_db = SessionDB()
        self.transcriber = Transcriber()
        self.diarizer = Diarizer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.summarizer = Summarizer()
        self._saved_audio_path = None

    def upload_audio_file_in_db(
        self,
        audio_path: Optional[str] = None,
        file: Optional[UploadFile] = None,
        blob_name: Optional[str] = None
    ) -> str:
        if not blob_name:
            raise ValueError("blob_name must be provided for Azure upload.")

        if file:
            self._saved_audio_path = self.DBLoader.load_audio_from_file(file,blob_name)
        elif audio_path:
            self._saved_audio_path = self.DBLoader.load_audio(audio_path)
        else:
            raise ValueError("Either 'audio_path' or 'file' must be provided.")

        return self._saved_audio_path

    def process_audio(self, session_id: str, audio_path: Optional[str] = None):
        path_to_use = audio_path or self._saved_audio_path
        if not path_to_use:
            raise ValueError("No audio path provided or saved for processing.")

        try:
            print(f"📥 Processing audio: {path_to_use}")
            text = self.transcriber.transcribe(path_to_use)
            speaker_segments = self.diarizer.identify(path_to_use)
            emotions = self.emotion_analyzer.analyze(path_to_use, speaker_segments)
            speaker_ids = list(emotions.keys())
            summary = self.summarizer.generate(text, emotions, speaker_ids)

            self.session_db.update_session(session_id, {
                "transcript": text,
                "participants": list(set(speaker_ids)),
                "emotion_breakdown": emotions,
                "summary": summary,
                "status": "Ready",
                "processing_error": None
            })

            print("✅ Processing complete and saved to DB.")

        except Exception as e:
            print(f"❌ Processing failed: {e}")
            self.session_db.set_status(session_id, "Error", str(e))

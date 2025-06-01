from typing import Optional

from fastapi import UploadFile

from app.services.db_loader import DBLoader
from app.services.diarizer import Diarizer
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.emotions_analysis_manager import EmotionsAnalysisManager
from app.services.sessionDB import SessionDB
from app.services.summarizer import Summarizer
from app.services.transcribe_with_diarization_manager import TranscribeAndDiarizeManager
from app.services.transcriber import Transcriber


class DialogueProcessor:
    def __init__(self):
        self.DBLoader = DBLoader()
        self.session_db = SessionDB()
        #self.transcriber = Transcriber()
        self.transcriber = TranscribeAndDiarizeManager()
        self.diarizer = Diarizer()
        self.emotion_analyzer = EmotionsAnalysisManager()
        self.summarizer = Summarizer()
        self._saved_audio_path = None

    def upload_audio_file_in_db(
        self,
        audio_path: Optional[str] = None,
        file: Optional[UploadFile] = None
    ) ->  tuple[str, str]:

        if file:
            self.session_id, self._saved_audio_path = self.DBLoader.load_audio_from_file(file)

        elif audio_path:
            self.session_id = None
            self._saved_audio_path = self.DBLoader.load_audio(audio_path)
        else:
            raise ValueError("Either 'audio_path' or 'file' must be provided.")

        return self.session_id, self._saved_audio_path


    def process_audio(self, session_id: str, audio_path: Optional[str] = None):
        path_to_use = audio_path or self._saved_audio_path

        if not path_to_use:
            raise ValueError("No audio path provided or saved for processing.")

        print(f"📥 Processing audio: {path_to_use}")

        self.session_db.set_status(session_id, "transcript_status", "processing")

        try:
            transcriber_sas_url = self.transcriber.transcribe(path_to_use,session_id)
            self.session_db.set_status(session_id, "transcript_status", "completed")
            print("✅ Transcription complete.")

        except Exception as e:
            self.session_db.set_status(session_id, "transcript_status", "failed")
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Transcription failed: {e}")
            return

        self.session_db.set_status(session_id, "emotion_breakdown_status", "processing")

        try:
            emotions_url = self.emotion_analyzer.analyze(transcriber_sas_url, session_id)
            self.session_db.set_status(session_id, "emotion_breakdown_status", "completed")
            print("✅ Emotion complete.")
            # speaker_segments = self.diarizer.identify(path_to_use)

        except Exception as e:
            self.session_db.set_status(session_id, "emotion_breakdown_status", "failed")
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Emotion failed: {e}")
            return

        speaker_ids = list(emotions_url.keys())

        self.session_db.set_status(session_id, "summary_status", "processing")

        try:
            summary = self.summarizer.generate(transcriber_sas_url, emotions_url, speaker_ids)
            self.session_db.set_status(session_id, "summary_status", "completed")
            print("✅ Summarization complete.")

        except Exception as e:
            self.session_db.set_status(session_id, "summary_status", "failed")
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Emotion failed: {e}")
            return

        print("✅ Transcription, diarization, emotion analysis, and summarization complete.")

        try:
            self.session_db.update_session(session_id, {
                "transcript": transcriber_sas_url,
                "participants": list(set(speaker_ids)),
                "emotion_breakdown": emotions_url,
                "summary": summary,
                "status": "Ready",
                "processing_error": None
            })

        except Exception as e:
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Failed to save session data: {e}")
            return

        print("✅ Processing complete and saved to DB.")
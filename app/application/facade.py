from __future__ import annotations
import uuid
from typing import Any, Dict, Optional

from app.application.queues import TaskQueue
from app.core.constants.db.supabase_constants import SessionColumn, SessionStatus
from app.interfaces.logic.pipeline import PipelineInput
from app.logic.dialogueDNA.pipeline import DialogueDNAPipeline
from app.state.app_states import AppState

from app.application.reporter_factory import ReporterFactory

class ApplicationFacade:
    """
    Application Facade / Use-case layer for session workflows.
    Keeps domain (DialogueDNALogic) pure and orchestrates cross-cutting concerns
    like reporting, storage uploads, and DB status updates.
    """

    def __init__(self, app: AppState):
        self._app = app
        self._logic = DialogueDNAPipeline(app.services)
        self._reporters = ReporterFactory(app.database, app.storage)

    # ------------------------------------ Create ------------------------------------

    # ---------- Full Pipeline ----------

    def create_and_analyze(
            self,
            user_id: str,
            title: str,
            audio_local_path: str,
            *,
            inline_save: bool = False,
            dispatch: str = "thread",
            queue: TaskQueue
    )-> Dict[str, Any]:

        session_id, audio_blob_path = self.create_new_session(
            user_id=user_id,
            title=title,
            audio_local_path=audio_local_path
        )
        return self.analyze_session_dna(
            session_id=session_id,
            user_id=user_id,
            audio_path=audio_blob_path,
            inline_save=inline_save,
            dispatch=dispatch,
            queue=queue
        )

    def create_new_session(
            self,
            user_id: str,
            title: str,
            audio_local_path: str) -> tuple[str, str]:

        session_id = str(uuid.uuid4())

        # TODO: After fixing the upload in the storage, uncommand this line
        audio_blob_path = self._app.storage.client.upload(audio_local_path)

        record = {
            SessionColumn.session_id: session_id,
            SessionColumn.user_id: user_id,
            SessionColumn.title: title,
            SessionColumn.audio_file_url: audio_blob_path,
        }
        self._app.database.sessions_repo.create(record)
        return session_id, audio_blob_path

    def analyze_session_dna(
            self,
            session_id: str,
            user_id: str,
            *,
            audio_path: str = None,
            inline_save: bool = False,
            dispatch: str = "thread",
            queue: TaskQueue = None,
    ) -> Dict[str, Any]:

        # If audio_path is None, try to find it in the database
        if not audio_path:
            session = self._app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)
            if not session:
                raise ValueError("Session not found")
            audio_path = session.get(SessionColumn.audio_file_url, None)
            if not audio_path:
                raise ValueError("Audio file path not found")

        if queue is None:
            # Analyze in synchronize way
            self._run_full_pipeline(
                session_id=session_id,
                audio_path=audio_path,
                inline_save=inline_save,
                dispatch=dispatch
            )
        else:
            #  Analyze in asynchronize way - Enqueue job (pure function signature -> serializable for external queues)
            queue.enqueue(
                self._run_full_pipeline,
                self._app,
                session_id,
                audio_path,
                inline_save,
                dispatch,
            )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id)

    def _run_full_pipeline(
            self,
            session_id: str,
            audio_path: str,
            inline_save: bool,
            dispatch: str,
    ) -> None:

        # Build new session reporter
        reporter = self._reporters.for_session(
            session_id=session_id,
            inline_save=inline_save,
            dispatch=dispatch,
        )

        # Run pipeline
        pipeline_results = self._logic.run(PipelineInput(audio=audio_path, reporter=reporter))

        # # (Optional) Final update in case we didn't provide reporter
        # patch = {
        #     "status": "ready",
        #     "transcript":
        #         [
        #             {
        #                 "writer": s.writer,
        #                 "text": s.text,
        #                 "start": s.start_time,
        #                 "end": s.end_time
        #             }
        #             for s in pipeline_results.transcription
        #         ]
        #         if inline_save else None,
        #     "emotions":
        #         [
        #             {
        #                 "whom": s.whom,
        #                 "start": s.start_time,
        #                 "end": s.end_time,
        #                 "text": s.text,
        #                 "audio": s.audio,
        #                 "mixed": s.mixed
        #             }
        #             for s in pipeline_results.emotion_analysis
        #         ]
        #         if inline_save else None,
        #     "summary":
        #         [
        #             {
        #                 "summary": pipeline_results.summarization.summary,
        #                 "bullets": pipeline_results.summarization.bullets,
        #                 "per_speaker": pipeline_results.summarization.per_speaker,
        #                 "usage": pipeline_results.summarization.usage,
        #             }
        #         ]
        #         if inline_save else None,
        # }
        #
        # # Remove nones from patch
        # patch = {k: v for k, v in patch.items() if v is not None}
        # if patch:
        #     self.app.database.sessions_repo.update(session_id, patch)

    # ------------------------------------ Update ------------------------------------

    # ---------- Rebuilders ----------

    # REBUILD: only transcript on existing audio
    def rebuild_transcript(self, *, session_id: str, user_id: str) -> Dict[str, Any]:

        audio_local_path = self.get_audio(
            session_id=session_id,
            user_id=user_id
        )

        reporter = self._reporters.for_session(session_id=session_id)

        self._logic.transcribe(
            audio=audio_local_path,
            reporter=reporter
        )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id)

    # REBUILD: only emotions on existing audio and transcript
    def rebuild_emotions(self, *, session_id: str, user_id: str) -> Dict[str, Any]:

        audio_local_path = self.get_audio(
            session_id=session_id,
            user_id=user_id
        )

        transcription = self.get_transcript(
            session_id=session_id,
            user_id=user_id
        )

        if not transcription:
            transcription = self.rebuild_transcript(
                session_id=session_id,
                user_id=user_id
            )

        reporter = self._reporters.for_session(session_id=session_id)

        self._logic.analyze_emotions_on_transcript(
            audio=audio_local_path,
            transcription=transcription,
            reporter=reporter
        )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id)

    # REBUILD: only summary on existing audio, transcript and emotions
    def rebuild_summary(self, *, session_id: str, user_id: str, style: str, max_token: Optional[int] = None,
                        language_hint: Optional[str] = None, inline_save: bool = False,
                        per_speaker: Optional[bool] = None, bullets: Optional[bool] = None,
                        metadata: Optional[Dict[str, str]] = None
                        ) -> Dict[str, Any]:

        analyzed_emotions = self.get_analyzed_emotions(
            session_id=session_id,
            user_id=user_id,
        )

        if not analyzed_emotions:
            analyzed_emotions = self.rebuild_emotions(
                session_id=session_id,
                user_id=user_id,
            )

        self._logic.summarize(
            segments=analyzed_emotions,
            style=style,
            max_tokens=max_token,
            language=language_hint,
            per_speaker=per_speaker,
            bullets=bullets,
            metadata=metadata
        )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id)

    # ------------------------------------ Read ------------------------------------

    def get_session(self, session_id: str, user_id: str):
        session = self._app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)

        if not session:
            raise ValueError("Session not found")

        return session

    def get_audio(self, session_id: str, user_id: str):
        session = self.get_session(session_id=session_id, user_id=user_id)

        audio_status: SessionStatus = session.get(SessionColumn.audio_file_status, None)

        if audio_status is not SessionStatus.completed:
            return None

        audio_file_url: str = session.get(SessionColumn.audio_file_url, None)

        if not audio_file_url:
            raise ValueError("audio file url not found")

        # TODO: Fix the download in the storage
        try:
            audio = self._app.storage.client.download(audio_file_url)
        except Exception as e:
            raise ValueError("Failed to download audio: {}".format(e))

        # TODO: Save in temp file and return the audio local path

        return audio

    def get_transcript(self, session_id: str, user_id: str):

        session = self.get_session(session_id=session_id, user_id=user_id)

        transcript_status: SessionStatus = session.get(SessionColumn.transcript_status, None)

        if transcript_status is not SessionStatus.completed:
            return None

        transcript_url: str = session.get(SessionColumn.transcript_url, None)

        if not transcript_url:
            raise ValueError("transcript url not found")

        # TODO: Fix the download in the storage
        try:
            transcription = self._app.storage.client.download(transcript_url)
        except Exception as e:
            raise ValueError("Failed to download transcription: {}".format(e))

        return transcription

    def get_analyzed_emotions(self, session_id: str, user_id: str):

        session = self.get_session(session_id=session_id, user_id=user_id)

        analyzed_emotions_status: SessionStatus = session.get(SessionColumn.emotion_breakdown_status, None)

        if analyzed_emotions_status is not SessionStatus.completed:
            return None

        analyzed_emotions_url: str = session.get(SessionColumn.emotion_breakdown_url, None)

        if not analyzed_emotions_url:
            raise ValueError("analyzed emotions url not found")

        # TODO: Fix the download in the storage
        try:
            analyzed_emotions = self._app.storage.client.download(analyzed_emotions_url)
        except Exception as e:
            raise ValueError("Failed to download analyzed emotions: {}".format(e))

        return analyzed_emotions

    def get_summary(self, session_id: str, user_id: str):

        session = self.get_session(session_id=session_id, user_id=user_id)

        summary_status: SessionStatus = session.get(SessionColumn.summary_status, None)

        if summary_status is not SessionStatus.completed:
            return None

        summary_url: str = session.get(SessionColumn.summary_url, None)

        if not summary_url:
            raise ValueError("analyzed emotions url not found")

        # TODO: Fix the download in the storage
        try:
            summarization = self._app.storage.client.download(summary_url)
        except Exception as e:
            raise ValueError("Failed to download summary: {}".format(e))

        return summarization

    def get_sessions(self, user_id: str):
        return self._app.database.sessions_repo.list_for_user(user_id)

    # ------------------------------------ Delete ------------------------------------

    def delete_session(self, session_id: str, user_id: str):
        return self._app.database.sessions_repo.delete(user_id)


from __future__ import annotations
import uuid
from typing import Any, Dict, Optional, List, Mapping

from app.application.queues import TaskQueue
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
        self.app = app
        self._logic = DialogueDNAPipeline(app.services)
        self._reporters = ReporterFactory(app.database, app.storage)

    def create_and_analyze(self, *, user_id: str, title: str, audio_path: str,
                           inline_save: bool = False, dispatch: str = "thread"
                           ) -> Dict[str, Any]:

        # Create new session
        session_id = self._create_new_session(user_id=user_id, title=title, audio_path=audio_path)

        # Analyze in synchronize way
        self._analyze_job(
            session_id=session_id,
            audio_path=audio_path,
            inline_save=inline_save,
            dispatch=dispatch
        )

        # Returns the updated session
        return self.app.database.sessions_repo.get_for_user(session_id, user_id)

    def enqueue_analysis(self, *, user_id: str, title: str, audio_path: str,
                         inline_save: bool = False, dispatch: str = "thread", queue: TaskQueue
                         )-> Dict[str, Any]:

        # Create new session
        session_id = self._create_new_session(user_id=user_id, title=title, audio_path=audio_path)

        # Enqueue job (pure function signature -> serializable for external queues)
        queue.enqueue(
            self._analyze_job,
            self.app,
            session_id,
            audio_path,
            inline_save,
            dispatch,
        )

        # Returns the updated session
        return self.app.database.sessions_repo.get_for_user(session_id, user_id)

    def _create_new_session(self, user_id: str, title: str, audio_path: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        record = {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "audio_path": audio_path,
            "status": "processing"
        }
        self.app.database.sessions_repo.create(record)
        return session_id

    def _analyze_job(
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

    # ---------- REBUILD: only emotions on existing transcript ----------
    def rebuild_emotions(self, *, session_id: str, user_id: str,
            fuse_weight_text: float = 0.5, fuse_weight_audio: float = 0.5,
            always_enhance_non_overlap: bool = False, dispatch: str = "thread",
            inline_save: bool = False,
    ) -> Dict[str, Any]:

        session = self.app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)

        if not session:
            raise ValueError("Session not found")

        audio_path: str = session.get("audio", None)
        transcript_rows: List[Mapping[str, Any]] = session.get("transcript", None)

        if not audio_path or not transcript_rows:
            raise ValueError("audio path or transcript not found")

        reporter = self._reporters.for_session(
            session_id=session_id,
            inline_save=inline_save,
            dispatch=dispatch,
        )

        emotions = self._logic.analyze_emotions_on_transcript(
            audio=audio_path,
            transcription=transcript_rows,
            reporter=reporter
        )

        patch: Dict[str, Any] = {"status": "emotions_ready"}
        if inline_save:
            patch["emotions"] = emotions
        self.app.database.sessions_repo.update(session_id, patch)

        return self.app.database.sessions_repo.get_for_user(session_id, user_id)

    # ---------- REBUILD: only summary (using current transcript+emotions) ----------
    def rebuild_summary(self, *, session_id: str, user_id: str, style: str, max_token: Optional[int] = None,
                        language_hint: Optional[str] = None, inline_save: bool = False,
                        per_speaker: Optional[bool] = None, bullets: Optional[bool] = None,
                        metadata: Optional[Dict[str, str]] = None
                        ) -> Dict[str, Any]:

        session = self.app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)

        if not session:
            raise ValueError("Session not found")

        emotions_rows: List[Mapping[str, Any]] = session.get("emotions", [])

        summary = self._logic.summarize(
            segments=emotions_rows,
            style=style,
            max_tokens=max_token,
            language=language_hint,
            per_speaker=per_speaker,
            bullets=bullets,
            metadata=metadata
        )

        patch: Dict[str, Any] = {"status": "summary_ready"}
        if inline_save:
            patch["summary"] = summary
        self.app.database.sessions_repo.update(session_id, patch)

        return self.app.database.sessions_repo.get_for_user(session_id, user_id)
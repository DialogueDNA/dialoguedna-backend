from app.api.auth import UserContext
from app.services.authz import AuthZ

class ServicesAPI:
    def __init__(self, logic, load_user_defaults, authz: AuthZ):
        self._logic = logic
        self._load_user_defaults = load_user_defaults
        self._authz = authz

    def transcribe(self, ctx: UserContext, container: str, blob: str, *,
                   locale: str | None = None, diarization: bool | None = None, backend: str | None = None):
        self._authz.require(ctx, "transcription:run")
        params = {"locale": locale or ctx.locale or "en-US", "diarization": True if diarization is None else bool(diarization)}
        if not backend and self._load_user_defaults:
            d = self._load_user_defaults(ctx.id) or {}
            backend = d.get("default_transcription_backend", backend)
            if isinstance(d.get("default_transcription_params"), dict):
                params.update(d["default_transcription_params"])
        tr = self._default_transcriber if not backend else self._build_transcriber(backend)
        return tr.transcribe_blob(container, blob, locale=params["locale"], speaker_diarization=params["diarization"])

    def transcribe_session(self, ctx: UserContext, session_id: str, *, backend: str | None = None, params: dict | None = None):
        self._authz.require(ctx, "transcription:run")
        return self._logic.transcribe_only(session_id, backend=backend, params=params or {})

    async def upload_audio_for_session(self, ctx: UserContext, file):
        self._authz.require(ctx, "sessions:upload")
        return await self._logic.upload_audio(file)

    def run_full_pipeline(self, ctx: UserContext, session_id: str, *, backend: str | None = None, params: dict | None = None):
        self._authz.require(ctx, "dialogue:process")
        return self._logic.process_audio(session_id, backend=backend, params=params or {})

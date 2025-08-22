from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.get("/{session_id}/audio", summary="Get audio location/URL for a session (if stored)")
def get_audio(req: Request, session_id: str):
    # If you store audio externally, expose a URL here
    storage = getattr(req.app.state.api, "storage", None)
    s = req.app.state.api.database.sessions_repo.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    audio_ref = s.get("audio_url") or s.get("audio_path")
    if storage and hasattr(storage, "client") and hasattr(storage.client, "get_url") and audio_ref:
        try:
            return {"audio_url": storage.client.get_url(audio_ref)}
        except Exception:
            pass
    # Fall back: return whatever is recorded
    if audio_ref:
        return {"audio": audio_ref}
    raise HTTPException(status_code=404, detail="Audio not available")

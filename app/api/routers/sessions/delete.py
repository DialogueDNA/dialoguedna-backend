from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.delete("/{session_id}", summary="Delete a session (and optionally its blobs)")
def delete_session(req: Request, session_id: str):
    repo = req.app.state.api.database.sessions_repo
    s = repo.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Optional: also delete blobs if you store audio/transcripts externally
    storage = getattr(req.app.state.api, "storage", None)
    audio_ref = s.get("audio_url") or s.get("audio_path")
    if storage and hasattr(storage, "client") and hasattr(storage.client, "delete") and audio_ref:
        try:
            storage.client.delete(audio_ref)
        except Exception:
            pass

    ok = repo.delete(session_id)
    return {"deleted": bool(ok)}

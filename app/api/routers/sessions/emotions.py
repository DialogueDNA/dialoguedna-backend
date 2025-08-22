from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.get("/{session_id}/emotions", summary="Get per-segment emotions (text/audio/fused)")
def get_emotions(req: Request, session_id: str):
    s = req.app.state.api.database.sessions_repo.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"emotions": s.get("emotions")}

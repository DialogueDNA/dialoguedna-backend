from fastapi import APIRouter, Request, HTTPException, Depends

from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user

router = APIRouter()

@router.get("/{session_id}/transcript", summary="Get transcript for a session")
def get_transcript(
        req: Request,
        session_id: str,
        ctx: UserContext = Depends(require_user)):
    s = req.app.state.api.database.sessions_repo.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"transcript": s.get("transcript")}

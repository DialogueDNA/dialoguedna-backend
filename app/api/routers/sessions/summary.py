from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.get("/{session_id}/summary", summary="Get summary for a session")
def get_summary(req: Request, session_id: str):
    s = req.app.state.api.database.sessions_repo.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"summary": s.get("summary")}

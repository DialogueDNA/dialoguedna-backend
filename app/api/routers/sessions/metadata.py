from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()

class UpdateMetadata(BaseModel):
    title: str

@router.patch("/{session_id}/metadata", summary="Update session metadata (e.g., title)")
def update_metadata(req: Request, session_id: str, body: UpdateMetadata):
    repo = req.app.state.api.database.sessions_repo
    if not repo.get(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    updated = repo.update(session_id, {"title": body.title})
    return {"session": updated}

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.application.facade import ApplicationFacade

router = APIRouter()

class UpdateMetadata(BaseModel):
    title: str

@router.get("/{session_id}/metadata", summary="Update session metadata (e.g., title)")
def get_metadata(
        session_id: str,
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)):
    try:
        return facade.get_session(
            session_id=session_id,
            user_id=ctx.id
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
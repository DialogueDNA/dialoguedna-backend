import logging

from fastapi import APIRouter, HTTPException, Depends

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.application.facade import ApplicationFacade

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{session_id}/audio", summary="Get audio location/URL for a session (if stored)")
def get_audio(
    session_id: str,
    facade: ApplicationFacade = Depends(get_facade),
    ctx: UserContext = Depends(require_user)):
    try:
        return facade.get_audio(
            session_id=session_id,
            user_id=ctx.id
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

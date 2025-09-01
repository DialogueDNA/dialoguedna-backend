from fastapi import APIRouter, HTTPException, Depends

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.api.mappers.artifacts_mapper import to_audio_response
from app.api.schemas.schemas import AudioResponse
from app.application.facade import ApplicationFacade

router = APIRouter()

@router.get("/{session_id}/audio", response_model=AudioResponse ,summary="Get audio location/URL for a session (if stored)")
def get_audio(
        session_id: str,
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)):
    try:
        return to_audio_response(facade.get_audio_view(session_id=session_id, user_id=ctx.id))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

from fastapi import APIRouter, HTTPException, Depends

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.api.mappers.artifacts_mapper import to_transcript_response
from app.api.schemas.schemas import TranscriptResponse
from app.application.facade import ApplicationFacade

router = APIRouter()

@router.get("/{session_id}/transcript", response_model=TranscriptResponse ,summary="Get transcript for a session")
def get_transcript(
        session_id: str,
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)):
    try:
        return to_transcript_response(facade.get_transcript_view(session_id=session_id, user_id=ctx.id))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

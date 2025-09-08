from fastapi import APIRouter, HTTPException, Depends

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.api.mappers.artifacts_mapper import to_analyzed_emotions_response
from app.api.schemas.schemas import AnalyzedEmotionsResponse
from app.application.facade import ApplicationFacade

router = APIRouter()

@router.get("/{session_id}/emotions", response_model=AnalyzedEmotionsResponse ,summary="Get per-segment emotions (text/audio/fused)")
def get_emotions(
        session_id: str,
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)):
    try:
        return to_analyzed_emotions_response(facade.get_analyzed_emotions_view(facade.get_analyzed_emotions_url(session_id=session_id, user_id=ctx.id)))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

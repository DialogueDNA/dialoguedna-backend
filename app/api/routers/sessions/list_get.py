from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies.authz import require_user
from app.api.dependencies.auth import UserContext
from app.application.facade import ApplicationFacade
from app.api.schemas.schemas import SessionListResponse, SessionResponse
from ...dependencies.app_facade import get_facade
from ...mappers.session_mapper import to_session_dto

router = APIRouter()

@router.get("", response_model=SessionListResponse, summary="List my sessions")
def list_sessions(
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)):
    try:
        return to_session_dto(facade.get_sessions(
            user_id=ctx.id
        ))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{session_id}", response_model=SessionResponse, summary="Get my session")
def get_session(
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

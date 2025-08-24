from fastapi import APIRouter, Request, HTTPException, Depends

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.application.facade import ApplicationFacade

router = APIRouter()

@router.delete("/{session_id}", summary="Delete a session (and optionally its blobs)")
def delete_session(
        session_id: str,
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)):
    try:
        return facade.delete_session(
            session_id=session_id,
            user_id=ctx.id
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
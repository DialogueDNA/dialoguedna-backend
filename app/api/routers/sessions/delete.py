from fastapi import APIRouter, HTTPException, Depends
from starlette import status

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.application.facade import ApplicationFacade

router = APIRouter()

@router.delete("/{session_id}", summary="Delete a session (and optionally its blobs)", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
        session_id: str,
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)):
    try:
        facade.delete_session(
            session_id=session_id,
            user_id=ctx.id
        )
        return
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
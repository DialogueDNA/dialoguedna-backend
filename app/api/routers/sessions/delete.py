from fastapi import APIRouter, HTTPException, Depends, Query, Body
from starlette import status

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.api.schemas.schemas import BulkDeleteRequest
from app.application.facade import ApplicationFacade

router = APIRouter()

@router.delete(path="/{session_id}", summary="Delete a session (and optionally its blobs)", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    delete_blobs: bool = Query(False, description="Also delete its blobs"),
    facade: ApplicationFacade = Depends(get_facade),
    ctx: UserContext = Depends(require_user),
):
    try:
        facade.delete_session(session_id=session_id, user_id=ctx.id, delete_blobs=delete_blobs)
        return
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete(path="", summary="Delete sessions for current user (and optionally their blobs)", status_code=status.HTTP_204_NO_CONTENT)
def delete_sessions(
    req: BulkDeleteRequest = Body(...),
    facade: ApplicationFacade = Depends(get_facade),
    ctx: UserContext = Depends(require_user),
):
    try:
        facade.delete_sessions(session_ids=req.session_ids, user_id=ctx.id, delete_blobs=req.delete_blobs)
        return
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))




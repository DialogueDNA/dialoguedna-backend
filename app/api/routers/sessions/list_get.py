from fastapi import APIRouter, Request, Depends
from app.api.dependencies.authz import require_user
from app.api.dependencies.auth import UserContext
from .schemas import SessionListResponse, SessionResponse

router = APIRouter()

@router.get("", response_model=SessionListResponse, summary="List my sessions")
def list_sessions(req: Request, ctx: UserContext = Depends(require_user)):
    repo = req.app.state.api.database.sessions_repo
    items = repo.list_for_user(ctx.id)  # ← user-filtered
    return {"sessions": items}

@router.get("/{session_id}", response_model=SessionResponse, summary="Get my session")
def get_session(session=Depends(...)):
    # use the ownership dep:
    from app.api.dependencies.resources import get_owned_session_or_404
    s = Depends(get_owned_session_or_404)  # or inject directly in signature
    return {"session": s}

from fastapi import Depends, HTTPException, Request
from app.api.dependencies.auth import user_context, UserContext

def get_owned_session_or_404(
    session_id: str,
    req: Request,
    ctx: UserContext = Depends(user_context),
):
    """Return the session document if it belongs to the current user; else 404."""
    repo = req.app.state.api.database.sessions_repo
    s = repo.get_for_user(session_id, ctx.id)  # atomic, prevents data leak
    if not s:
        # 404 instead of 403 to avoid leaking existence of others' sessions
        raise HTTPException(status_code=404, detail="Session not found")
    return s

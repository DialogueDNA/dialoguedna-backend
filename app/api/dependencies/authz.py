from fastapi import Depends, HTTPException
from typing import Iterable
from app.api.dependencies.auth import user_context, UserContext

def require_user(ctx: UserContext = Depends(user_context)) -> UserContext:
    """Require an authenticated user; returns the UserContext."""
    return ctx

def require_roles(roles: Iterable[str]):
    """Factory: ensure user has at least one of the required roles."""
    roles = set(roles)
    def _dep(ctx: UserContext = Depends(user_context)) -> UserContext:
        if not roles.intersection(set(ctx.roles or ())):
            raise HTTPException(status_code=403, detail="Forbidden (role)")
        return ctx
    return _dep

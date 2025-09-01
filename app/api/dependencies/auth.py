from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.jwt_verifier import JWTVerifier

bearer_scheme = HTTPBearer()
_verifier = JWTVerifier()

def _unauthorized(msg="Not authenticated"):
    return HTTPException(
        status_code=401, detail=msg, headers={"WWW-Authenticate": "Bearer"}
    )

def get_jwt_claims(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if credentials is None or (credentials.scheme or "").lower() != "bearer":
        raise _unauthorized()
    token = credentials.credentials
    try:
        claims = _verifier.verify_and_decode(token)
        return claims
    except Exception:
        raise _unauthorized("Invalid token")

# ---- UserContext ----
from dataclasses import dataclass
from typing import Optional, Sequence

@dataclass(frozen=True)
class UserContext:
    id: str
    org_id: Optional[str] = None
    roles: Sequence[str] = ()
    plan: Optional[str] = None
    locale: Optional[str] = None

def user_context(claims=Depends(get_jwt_claims)) -> UserContext:
    uid = claims.get("sub")
    if not uid:
        raise HTTPException(401, "Invalid token (sub missing)")
    return UserContext(
        id=uid,
        org_id=claims.get("org_id") or claims.get("tenant") or claims.get("organization_id"),
        roles=claims.get("roles", []),
        plan=claims.get("plan") or claims.get("tier") or "free",
        locale=claims.get("locale") or "en-US",
    )

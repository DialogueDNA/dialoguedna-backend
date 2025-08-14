from __future__ import annotations
import time, json, urllib.request
from typing import Any, Dict, Optional

from jose import jwt
from app.core.environment import (
    AUTH_JWT_ALG, AUTH_JWT_SECRET, AUTH_JWT_PUBLIC_KEY, AUTH_JWKS_URL, AUTH_JWT_ISS, AUTH_JWT_AUD
)

class JWTVerifier:
    def __init__(self) -> None:
        self.alg = AUTH_JWT_ALG.upper()
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_fetched_at: Optional[float] = None
        self._jwks_ttl = 300  # 5 דקות cache

    def _get_key(self, headers: Dict[str, Any]) -> str:
        if self.alg == "HS256":
            if not AUTH_JWT_SECRET:
                raise RuntimeError("AUTH_JWT_SECRET missing for HS256")
            return AUTH_JWT_SECRET

        if self.alg == "RS256" and AUTH_JWT_PUBLIC_KEY:
            return AUTH_JWT_PUBLIC_KEY

        kid = headers.get("kid")
        if not AUTH_JWKS_URL:
            raise RuntimeError("AUTH_JWKS_URL missing for RS256/JWKS")

        now = time.time()
        if not self._jwks_cache or not self._jwks_fetched_at or (now - self._jwks_fetched_at) > self._jwks_ttl:
            with urllib.request.urlopen(AUTH_JWKS_URL) as resp:
                self._jwks_cache = json.loads(resp.read().decode("utf-8"))
                self._jwks_fetched_at = now

        keys = self._jwks_cache.get("keys", [])
        for k in keys:
            if k.get("kid") == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
        raise RuntimeError("Signing key not found in JWKS")

    def verify_and_decode(self, token: str) -> Dict[str, Any]:
        headers = jwt.get_unverified_header(token)
        key = self._get_key(headers)

        opts = {
            "verify_aud": bool(AUTH_JWT_AUD),
            "verify_iss": bool(AUTH_JWT_ISS),
        }
        claims = jwt.decode(
            token,
            key,
            algorithms=[self.alg],
            audience=AUTH_JWT_AUD if AUTH_JWT_AUD else None,
            issuer=AUTH_JWT_ISS if AUTH_JWT_ISS else None,
            options=opts
        )
        return claims

from __future__ import annotations
from fastapi import APIRouter, Request, HTTPException, Body
from typing import Optional

router = APIRouter(prefix="/me/defaults", tags=["user-defaults"])

def _get_user_id(req: Request) -> str:
    # Adjust this to your auth layer. If you use Supabase auth, fetch from JWT claims.
    uid = getattr(req.state, "user_id", None)
    if not uid:
        # fallback: try headers (demo). Replace with your auth mechanism.
        uid = req.headers.get("x-user-id")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized: user id missing")
    return uid

@router.get("")
def get_defaults(req: Request):
    uid = _get_user_id(req)
    repo = getattr(req.app.state, "user_defaults_repo", None)
    if repo is None:
        raise HTTPException(status_code=500, detail="user_defaults_repo not wired")
    data = repo.get(uid) or {}
    return {"user_id": uid, "defaults": data}

@router.put("")
def upsert_defaults(req: Request,
                    default_transcription_backend: Optional[str] = Body(None),
                    default_transcription_params: Optional[dict] = Body(None),
                    default_emotion_backend: Optional[str] = Body(None),
                    default_emotion_params: Optional[dict] = Body(None),
                    default_summarizer_backend: Optional[str] = Body(None),
                    default_summarizer_params: Optional[dict] = Body(None),
                    default_locale: Optional[str] = Body(None)):
    uid = _get_user_id(req)
    repo = getattr(req.app.state, "user_defaults_repo", None)
    if repo is None:
        raise HTTPException(status_code=500, detail="user_defaults_repo not wired")
    payload = {
        k: v for k, v in {
            "default_transcription_backend": default_transcription_backend,
            "default_transcription_params": default_transcription_params,
            "default_emotion_backend": default_emotion_backend,
            "default_emotion_params": default_emotion_params,
            "default_summarizer_backend": default_summarizer_backend,
            "default_summarizer_params": default_summarizer_params,
            "default_locale": default_locale,
        }.items() if v is not None
    }
    data = repo.upsert(uid, payload)
    return {"ok": True, "defaults": data}
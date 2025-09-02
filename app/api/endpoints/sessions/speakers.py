from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import requests

from app.api.dependencies.auth import get_current_user
from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage

router = APIRouter(prefix="/api/sessions", tags=["sessions:speakers"])

session_db = SessionDB()
storage = SessionStorage()

class SpeakersPayload(BaseModel):
    map: Dict[str, str] = Field(default_factory=dict)

@router.get("/{session_id}/speakers")
def get_speakers(session_id: str, current_user: dict = Depends(get_current_user)):
    s = session_db.get_session(session_id)
    if not s or s["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    mapping = s.get("speaker_map") or {}


    detected: List[str] = []
    samples: Dict[str, str] = {}
    try:
        blob_path = s.get("transcript_url")
        if blob_path:
            url = blob_path if str(blob_path).startswith("http") else storage.generate_sas_url(blob_path)
            arr = requests.get(url, timeout=30).json()
            for entry in arr:
                spk = entry.get("speaker")
                if spk is None:
                    continue
                spk = str(spk)
                if spk not in detected:
                    detected.append(spk)
                    samples[spk] = (entry.get("text") or "")[:120]
                if len(detected) >= 12:
                    break
    except Exception:
        pass

    return {"map": mapping, "detected": detected, "samples": samples}

@router.put("/{session_id}/speakers")
def put_speakers(session_id: str, body: SpeakersPayload, current_user: dict = Depends(get_current_user)):
    s = session_db.get_session(session_id)
    if not s or s["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    clean = {str(k): v.strip() for k, v in (body.map or {}).items() if isinstance(v, str) and v.strip()}
    for name in clean.values():
        if len(name) > 32:
            raise HTTPException(status_code=400, detail="Speaker names must be ≤ 32 chars")

    session_db.update_session(session_id, {"speaker_map": clean or None})
    return {"map": clean}

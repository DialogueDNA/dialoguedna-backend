from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
import requests

from app.api.dependencies.auth import get_current_user
from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage

router = APIRouter()  # <— no prefix here; prefix is added by sessions/__init__.py

session_db = SessionDB()
storage = SessionStorage()

class SpeakersPayload(BaseModel):
    map: Dict[str, str] = Field(default_factory=dict)

def _collect_detected_and_samples(session):
    detected: List[str] = []
    samples: Dict[str, str] = {}
    try:
        blob_path = session.get("transcript_url")
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
    return detected, samples

@router.get("/{session_id}")
def get_speakers(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    GET /api/sessions/speakers/{session_id}
    Returns: { map: {...}, detected: [...], samples: {...} }
    """
    s = session_db.get_session(session_id)
    if not s or s["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    mapping = s.get("speaker_map") or {}
    detected, samples = _collect_detected_and_samples(s)
    return {"map": mapping, "detected": detected, "samples": samples}

@router.put("/{session_id}")
def put_speakers(session_id: str, body: SpeakersPayload, current_user: dict = Depends(get_current_user)):
    s = session_db.get_session(session_id)
    if not s or s["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    clean = {str(k): v.strip() for k, v in (body.map or {}).items() if isinstance(v, str) and v.strip()}
    for name in clean.values():
        if len(name) > 32:
            raise HTTPException(status_code=400, detail="Speaker names must be ≤ 32 chars")

    # build display participants list in speaker order we detected from transcript
    detected, _samples = _collect_detected_and_samples(s)  # already exists in this file
    # fallback if we couldn't detect: use sorted keys of mapping
    order = detected or sorted(clean.keys(), key=lambda x: int(x) if str(x).isdigit() else str(x))
    participants_display = [clean.get(k, f"Speaker {k}") for k in order]

    session_db.update_session(session_id, {
        "speaker_map": clean or None,
        "participants": participants_display or None,   # <— UPDATE participants for cards/list
    })
    return {"map": clean, "participants": participants_display}

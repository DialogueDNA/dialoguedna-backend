# app/services/summary/runner.py
"""
Summary auto-run trigger (idempotent).

Runs only when:
- transcript_status == 'completed'
- emotion_breakdown_status == 'completed'
- summary_status != 'completed'
- summary_preset is set

IMPORTANT:
- Load transcript/emotions from the *DB URLs* (transcript_url, emotion_breakdown_url)
  instead of guessing blob paths. This avoids 404/KeyErrors if filenames differ.
- Normalize preset to PromptStyle Enum before passing to Summarizer.
"""

import requests
from typing import Optional

from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage
from app.services.summary.summarizer import Summarizer
from app.services.summary.prompts import PromptStyle

session_db = SessionDB()
storage = SessionStorage()


def _safe_get_json_from_blob_path(blob_path: Optional[str]):
    """Turn a blob path (e.g. 'sid/transcript.json') into a signed URL and load JSON."""
    if not blob_path:
        return None
    url = storage.generate_sas_url(blob_path)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def try_run_summary(session_id: str) -> bool:
    """
    Return True if summary ran now, False otherwise.
    Idempotent: does nothing if summary_status == 'completed'.
    """
    s = session_db.get_session(session_id)
    if not s:
        return False

    # Do not re-run once completed
    if s.get("summary_status") == "completed":
        return False

    # Prerequisites
    if s.get("transcript_status") != "completed":
        return False
    if s.get("emotion_breakdown_status") != "completed":
        return False

    # Read preset from DB and normalize
    preset_str = s.get("summary_preset")
    if not preset_str:
        return False
    try:
        preset_enum = PromptStyle(preset_str)
    except ValueError:
        session_db.update_session(session_id, {
            "summary_status": "failed",
            "processing_error": f"Unknown summary_preset '{preset_str}'"
        })
        return False

    # Mark processing
    session_db.update_session(session_id, {"summary_status": "processing"})

    try:
        # <<< KEY FIX: load from DB URLs, not hard-coded paths >>>
        transcript_json = _safe_get_json_from_blob_path(s.get("transcript_url"))
        emotions_json   = _safe_get_json_from_blob_path(s.get("emotion_breakdown_url"))

        # Run summarizer with Enum (not str)
        summary_text = Summarizer().summarize(
            transcript=transcript_json,
            emotions=emotions_json,
            preset_key=preset_enum,
        )

        # Persist and mark done
        summary_blob = storage.store_summary(session_id, summary_text)
        session_db.update_session(session_id, {
            "summary_url": summary_blob,
            "summary_status": "completed",
            "processing_error": None
        })
        return True

    except Exception as e:
        session_db.update_session(session_id, {
            "summary_status": "failed",
            "processing_error": str(e),
        })
        return False

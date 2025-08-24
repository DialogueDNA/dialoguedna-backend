import logging

from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{session_id}/audio", summary="Get audio location/URL for a session (if stored)")
def get_audio(req: Request, session_id: str):
    try:
        return req.app.state.api.get_audio(session_id)
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=404, detail="Audio not available")

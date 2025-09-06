from typing import List

from app.api.schemas.schemas import SessionDTO, SessionResponse, SessionListResponse
from app.models.session import SessionDB

def to_session_dto(db: SessionDB) -> SessionDTO:
    return SessionDTO(
        id=str(db.id),
        title=db.title,
        audio_url=db.audio_file_url,
        transcript_url=db.transcript_url,
        emotions_url=db.emotion_breakdown_url,
        summary_url=db.summary_url,
        session_status=db.session_status,
        audio_status=db.audio_file_status,
        transcript_status=db.transcript_status,
        emotion_status=db.emotion_breakdown_status,
        summary_status=db.summary_status,
        duration=db.duration,
        language=db.language,
        participants=db.participants,
        created_at=db.created_at,
    )

# --------- Convenience wrappers for your typed API responses ---------

def to_session_response(payload: SessionDB) -> SessionResponse:
    return SessionResponse(session=to_session_dto(payload))

def to_sessions_response(list_of_sessions: List[SessionDB]) -> SessionListResponse:
    return SessionListResponse(sessions=[to_session_dto(session) for session in (list_of_sessions or [])])

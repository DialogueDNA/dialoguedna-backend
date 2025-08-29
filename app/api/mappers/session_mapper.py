from typing import List

from app.api.schemas.schemas import SessionDTO, TranscriptRowDTO, TranscriptDTO
from app.interfaces.services.text import TextSegment
from app.interfaces.services.transcription import TranscriptionOutput
from app.models.session import SessionDB

def to_transcript_segment(transcript_segment: TextSegment) -> TranscriptRowDTO:
    return TranscriptRowDTO(
        speaker=transcript_segment.writer,
        text=transcript_segment.text,
        start=transcript_segment.start_time,
        end=transcript_segment.end_time,
    )

def to_transcript(transcript: TranscriptionOutput) -> TranscriptDTO:
    return TranscriptDTO(
        transcript= [
            TranscriptRowDTO(
                text=segment.text,
                start=segment.start_time,
                end=segment.end_time,
                speaker=segment.writer,
            )
        for segment in transcript
        ]
    )

def to_session_dto(db: SessionDB) -> SessionDTO:
    return SessionDTO(
        id=str(db.id),
        title=db.title,
        audio_url=db.audio_url,
        transcript_url=db.transcript_url,
        emotions_url=db.emotions_url,
        summary_url=db.summary_url,
        duration=db.duration,
        language=db.language,
        participants=db.participants,
        audio_status=db.audio_status,
        emotion_status=db.emotion_status,
        transcript_status=db.transcript_status,
        summary_status=db.summary_status,
        created_at=db.created_at,
    )

def to_list_sessions_dto(list_of_sessions: List[SessionDB]) -> List[SessionDTO]:
    return [to_session_dto(session) for session in list_of_sessions]

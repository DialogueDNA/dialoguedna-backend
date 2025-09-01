from app.api.schemas.schemas import (
    ArtifactDTO,
    ArtifactAccess,
    AudioResponse,
    TranscriptResponse,
    AnalyzedEmotionsResponse,
    SummaryResponse,
    ProcessingStatus,
)
from typing import Any, Mapping, Optional
from datetime import datetime


def to_artifact_dto(payload: Mapping[str, Any]) -> ArtifactDTO:
    """
    Map a raw dict like:
      {
        "status": <status>,
        "result": {
          "blob_path": <str>,
          "sas_url": <str>,
          "expires_at": <str|datetime>
        }
      }
    into ArtifactDTO (status + ArtifactAccess | None).
    """
    status: ProcessingStatus = payload.get("status")  # pydantic will validate the literal
    result: Optional[Mapping[str, Any]] = payload.get("result")

    access = None
    if result:
        access = ArtifactAccess(
            object_path=result.get("blob_path"),
            access_url=result.get("sas_url"),
            # pydantic parses ISO strings to datetime automatically; pass through as-is
            expires_at=result.get("expires_at") if isinstance(result.get("expires_at"), datetime)
                      else result.get("expires_at"),
        )

    return ArtifactDTO(status=status, result=access)


# --------- Convenience wrappers for your typed API responses ---------

def to_audio_response(payload: Mapping[str, Any]) -> AudioResponse:
    """Wrap ArtifactDTO under the 'audio' field, per schemas."""
    return AudioResponse(audio=to_artifact_dto(payload))

def to_transcript_response(payload: Mapping[str, Any]) -> TranscriptResponse:
    """Wrap ArtifactDTO under the 'transcript' field, per schemas."""
    return TranscriptResponse(transcript=to_artifact_dto(payload))

def to_analyzed_emotions_response(payload: Mapping[str, Any]) -> AnalyzedEmotionsResponse:
    """Wrap ArtifactDTO under the 'analyzed_emotions' field, per schemas."""
    return AnalyzedEmotionsResponse(analyzed_emotions=to_artifact_dto(payload))

def to_summary_response(payload: Mapping[str, Any]) -> SummaryResponse:
    """Wrap ArtifactDTO under the 'summary' field, per schemas."""
    return SummaryResponse(summary=to_artifact_dto(payload))

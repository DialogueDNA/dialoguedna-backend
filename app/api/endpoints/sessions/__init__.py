# from fastapi import APIRouter
#
# from .metadata import router as metadata_router
# from .upload import router as upload_router
# from .transcript import router as transcript_router
# from .emotions import router as emotions_router
# from .summary import router as summary_router
# from .audio import router as audio_router
# from .delete import router as delete_router
#
# router = APIRouter()
#
# router.include_router(metadata_router, prefix="/api/sessions/metadata", tags=["metadata"])
# router.include_router(upload_router, prefix="/api/sessions/upload", tags=["upload"])
# router.include_router(transcript_router, prefix="/api/sessions/transcription", tags=["transcription"])
# router.include_router(emotions_router, prefix="/api/sessions/emotion_analysis", tags=["emotion_analysis"])
# router.include_router(summary_router, prefix="/api/sessions/summary", tags=["summary"])
# router.include_router(audio_router, prefix="/api/sessions/audio", tags=["audio"])
# router.include_router(delete_router, prefix="/api/sessions/delete", tags=["delete"])
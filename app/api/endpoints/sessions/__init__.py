from fastapi import APIRouter
from .metadata import router as metadata_router
from .audio import router as audio_router
from .upload import router as upload_router
from .transcript import router as transcript_router
from .emotions import router as emotions_router
from .summary import router as summary_router

router = APIRouter()

router.include_router(metadata_router, prefix="/api/metadata", tags=["metadata"])
router.include_router(audio_router, prefix="/api/audio", tags=["audio"])
router.include_router(upload_router, prefix="/api/upload", tags=["upload"])
router.include_router(transcript_router, prefix="/api/transcript", tags=["transcript"])
router.include_router(emotions_router, prefix="/api/emotions", tags=["emotions"])
router.include_router(summary_router, prefix="/api/summary", tags=["summary"])

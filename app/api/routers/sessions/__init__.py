from fastapi import APIRouter
from .upload import router as upload_router
from .list_get import router as list_get_router
from .transcript import router as transcript_router
from .emotions import router as emotions_router
from .summary import router as summary_router
from .metadata import router as metadata_router
from .audio import router as audio_router
from .delete import router as delete_router

router = APIRouter()
router.include_router(upload_router,     prefix="/api/sessions", tags=["sessions"])
router.include_router(list_get_router,   prefix="/api/sessions", tags=["sessions"])
router.include_router(transcript_router, prefix="/api/sessions", tags=["sessions"])
router.include_router(emotions_router,   prefix="/api/sessions", tags=["sessions"])
router.include_router(summary_router,    prefix="/api/sessions", tags=["sessions"])
router.include_router(metadata_router,   prefix="/api/sessions", tags=["sessions"])
router.include_router(audio_router,      prefix="/api/sessions", tags=["sessions"])
router.include_router(delete_router,     prefix="/api/sessions", tags=["sessions"])

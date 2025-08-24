import os
import shutil
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Depends, BackgroundTasks

from app.api.dependencies.app_facade import get_facade
from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user

from app.api.routers.sessions.schemas import SessionResponse
from app.application.facade import ApplicationFacade
from app.application.queues import BackgroundTasksQueue

router = APIRouter()

@router.post("", response_model=SessionResponse, summary="Create a session (background analyze)")
async def create_session(
        background: BackgroundTasks,
        file: UploadFile = File(...),
        title: str = Form(...),
        facade: ApplicationFacade = Depends(get_facade),
        ctx: UserContext = Depends(require_user)
):
    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[-1] or ".wav") as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(file.file, tmp)

    try:
        return facade.create_and_analyze(
            user_id=ctx.id,
            title=title,
            audio_local_path=tmp_path,
            inline_save=False,
            queue=BackgroundTasksQueue(background),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
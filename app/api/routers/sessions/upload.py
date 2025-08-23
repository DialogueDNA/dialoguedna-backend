from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Depends, BackgroundTasks
from tempfile import NamedTemporaryFile
import shutil, uuid, os

from app.api.dependencies.auth import UserContext
from app.api.dependencies.authz import require_user
from app.api.routers.sessions.schemas import SessionResponse
import app.core.constants.db.supabase_constants as db_constants

router = APIRouter()

@router.post("", response_model=SessionResponse, summary="Create a session (background analyze)")
async def create_session_bg(req: Request,
                            background: BackgroundTasks,
                            file: UploadFile = File(...),
                            title: str = Form(...),
                            ctx: UserContext = Depends(require_user)):

    # 1) Persist upload to a temp path (works for local/remote analyzers)
    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[-1]) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(file.file, tmp)


    session_id = str(uuid.uuid4())
    repo = req.app.state.api.database.sessions_repo
    created = repo.create({
        db_constants.SESSIONS_COLUMN_USER_ID: ctx.id,
        db_constants.SESSIONS_COLUMN_UNIQUE_ID: session_id,
        db_constants.SESSIONS_COLUMN_TITLE: title,
        db_constants.SESSIONS_COLUMN_STATUS: db_constants.SESSION_STATUS_PROGRESSING
    })

    def do_analyze(path: str, sid: str):
            req.app.state.logic.run(audio=path, diarization=True)


    background.add_task(do_analyze, tmp_path, session_id)
    return {"session": created}


@router.post("", response_model=SessionResponse)
async def create_session(req: Request,
                         file: UploadFile = File(...),
                         title: str = Form(...),
                         ctx: UserContext = Depends(require_user)):
    # TODO: Save in temp file
    # tmp_path = ...file...

    session = req.app.state.api.create_and_analyze(
        user_id=ctx.id,
        title=title,
        audio_path=tmp_path,
        inline_save=False,
        upload_blobs=True,
        dispatch="thread",
    )
    return {"session": session}

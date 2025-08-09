# app/api/sessions.py
from fastapi import APIRouter, Request

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/")
def create_session(req: Request, payload: dict):
    return req.app.state.sessions_repo.create(payload)

@router.get("/{session_id}")
def get_session(req: Request, session_id: str):
    return req.app.state.sessions_repo.get(session_id)

@router.get("/user/{user_id}")
def list_user_sessions(req: Request, user_id: str):
    return req.app.state.sessions_repo.list_for_user(user_id)

@router.put("/{session_id}")
def update_session(req: Request, session_id: str, updates: dict):
    return req.app.state.sessions_repo.update(session_id, updates)

@router.delete("/{session_id}")
def delete_session(req: Request, session_id: str):
    return req.app.state.sessions_repo.delete(session_id)

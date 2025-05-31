from fastapi import APIRouter, Depends, HTTPException
from app.core.config import supabase
from app.api.dependencies.auth import get_current_user

router = APIRouter()

# GET: all sessions for current user
@router.get("/")
def get_sessions(current_user: dict = Depends(get_current_user)):
    response = supabase.table("sessions").select("*").eq("user_id", current_user["id"]).execute()
    return response.data

# DELETE: a session + remove audio from storage
@router.delete("/{session_id}")
def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    print(session_id)
    session = supabase.table("sessions").select("audio_file_url").eq("id", session_id).eq("user_id", current_user["id"]).single().execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove audio file from Supabase Storage
    supabase.storage.from_("audio-sessions").remove([session.data["audio_file_url"]])

    # Remove session from Supabase DB
    supabase.table("sessions").delete().eq("id", session_id).execute()
    return {"message": "Session deleted successfully"}

import tempfile
from pydub import AudioSegment
from fastapi import UploadFile

def format_duration(seconds: float) -> str:
    """
    Converts duration in seconds to a human-readable format: H:MM:SS or M:SS.
    """
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def get_audio_duration(audio_file: UploadFile) -> dict:
    """
    Calculates the duration of an uploaded audio file and returns both raw seconds and formatted time.

    Parameters:
    - audio_file (UploadFile): The uploaded audio file from FastAPI.

    Returns:
    - dict: {
        "duration_seconds": float,
        "duration_formatted": str
      }
    """
    # Map MIME types to pydub-supported formats
    format_map = {
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/x-m4a": "m4a",
        "audio/aac": "aac",
        "audio/ogg": "ogg"
    }

    mime_type = audio_file.content_type
    audio_format = format_map.get(mime_type)
    if not audio_format:
        raise ValueError(f"Unsupported audio format: {mime_type}")

    audio_file.file.seek(0)

    with tempfile.NamedTemporaryFile(delete=True, suffix=f".{audio_format}") as temp_file:
        temp_file.write(audio_file.file.read())
        temp_file.flush()

        audio = AudioSegment.from_file(temp_file.name, format=audio_format)
        duration_seconds = len(audio) / 1000.0

        return {
            "duration_seconds": round(duration_seconds, 2),
            "duration_formatted": format_duration(duration_seconds)
        }

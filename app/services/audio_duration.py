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

def get_audio_duration(audio_file: UploadFile) -> str:
    """
    Calculates the duration of an uploaded audio file and returns it as a formatted string.

    Parameters:
    - audio_file (UploadFile): The uploaded audio file from FastAPI.

    Returns:
    - str: Duration in H:MM:SS or M:SS format.
    """
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        temp_file.write(audio_file.file.read())
        temp_file.flush()

        audio = AudioSegment.from_file(temp_file.name)
        duration_seconds = len(audio) / 1000.0

        return format_duration(duration_seconds)

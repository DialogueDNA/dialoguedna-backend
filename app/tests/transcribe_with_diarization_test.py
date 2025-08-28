# tests/transcribe_with_diarization_test.py


import subprocess
import shutil
import pytest
from pathlib import Path
from app.services.transcript.transcriber import Transcriber
from app.storage.azure.blob.azure_blob_service import AzureBlobService

def convert_to_pcm16_mono_16k(src: Path) -> Path:
    """
    Convert audio to WAV PCM s16le, mono, 16kHz using ffmpeg.
    Returns the path to the converted file.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found in PATH. Please install ffmpeg.")

    dst = src.with_name(src.stem + "_fixed.wav")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-ac", "1",           # mono
        "-ar", "16000",       # 16 kHz
        "-sample_fmt", "s16", # PCM 16-bit
        str(dst),
    ]
    # run ffmpeg quietly but fail on error
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr.decode(errors='ignore')}")
    return dst


@pytest.mark.integration
def test_transcription_with_diarization():
    """
    Integration test:
    1. Uploads local audio file to Azure Blob Storage under 'tests/' folder.
    2. Runs transcription with diarization.
    """

    # 📂 Local test audio file
    local_audio_path = Path(r"C:\Users\Yarden Daniel\PycharmProjects\dialoguedna-backend\app\tests\output_audio.wav")
    assert local_audio_path.exists(), f"Test audio file not found: {local_audio_path}"

    # 🎛️ Ensure correct format for Azure Speech
    fixed_audio_path = convert_to_pcm16_mono_16k(local_audio_path)
    assert fixed_audio_path.exists(), "Converted audio file missing."

    # 📤 Upload file to Azure under 'tests/' container path
    azure = AzureBlobService()
    blob_name = f"tests/{fixed_audio_path.name}"   # e.g. "tests/extracted_audio.wav"
    azure.upload_file(fixed_audio_path, blob_name)

    # (Optional) Get SAS for manual verification
    try:
        sas_url = azure.generate_sas_url(blob_name)
        print("SAS URL:", sas_url)
    except Exception:
        pass  # ignore if your service generates SAS only in Transcriber


    # 📝 Run transcription using blob path
    transcriber = Transcriber()
    result = transcriber.transcribe(blob_name)

    # ✅ Sanity checks
    assert isinstance(result, list), "Result should be a list of phrases"
    assert len(result) > 0, "Transcript should not be empty"


    first_line = result[0]
    for key in ("speaker", "text", "start_time", "end_time"):
        assert key in first_line, f"Missing '{key}' in transcript line."

    print("\n--- Transcription Result ---")
    for line in result:
        print(line)


if __name__ == "__main__":
    test_transcription_with_diarization()

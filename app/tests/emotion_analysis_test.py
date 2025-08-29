# tests/emotion_analysis_test.py

import subprocess
import shutil
import pytest
from pathlib import Path

from app.services.transcript.transcriber import Transcriber
from app.services.emotions.emotion_controller import EmotionController
from app.storage.azure.blob.azure_blob_service import AzureBlobService
import json


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
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr.decode(errors='ignore')}")
    return dst


@pytest.mark.integration
def test_emotion_analysis_end_to_end():
    """
    Integration test for emotion analysis:
    1) Convert local audio to 16k mono PCM16
    2) Upload to Azure (for transcriber use)
    3) Transcribe with diarization
    4) Run EmotionController with local fixed audio path (tone) and transcript (text)
    5) Print a few fused rows
    """

    # 1) Local audio file
    local_audio_path = Path(r"C:\Users\Yarden Daniel\PycharmProjects\dialoguedna-backend\app\tests\output_audio.wav")
    assert local_audio_path.exists(), f"Test audio file not found: {local_audio_path}"

    fixed_audio_path = convert_to_pcm16_mono_16k(local_audio_path)
    assert fixed_audio_path.exists(), "Converted audio file missing."

    # 2) Upload for the transcriber (blob path)
    azure = AzureBlobService()
    blob_name = f"tests/{fixed_audio_path.name}"
    azure.upload_file(fixed_audio_path, blob_name)

    # 3) Transcribe (using blob path)
    transcriber = Transcriber()
    transcript = transcriber.transcribe(blob_name)
    assert isinstance(transcript, list) and len(transcript) > 0, "Transcript should be a non-empty list"

    # 4) Emotion analysis (tone uses local fixed file path)
    controller = EmotionController()
    emotions = controller.get_emotions(transcript=transcript, audio_path=str(fixed_audio_path))

    assert isinstance(emotions, list) and len(emotions) > 0, "Emotions should be a non-empty list"
    first = emotions[0]
    for key in ("speaker", "start_time", "end_time", "text", "audio", "fused"):
        assert key in first, f"Missing '{key}' in emotion row"

    # 5) Save transcript and emotions JSON to the same Azure directory
    container_prefix = "tests/emotion_runs"
    run_dir = f"{container_prefix}/{fixed_audio_path.stem}"
    transcript_blob = f"{run_dir}/transcript.json"
    emotions_blob = f"{run_dir}/emotions.json"

    # Save transcript
    transcript_json_path = fixed_audio_path.with_name(f"{fixed_audio_path.stem}_transcript.json")
    transcript_json_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    azure.upload_file(transcript_json_path, transcript_blob)

    # Save emotions
    emotions_json_path = fixed_audio_path.with_name(f"{fixed_audio_path.stem}_emotions.json")
    emotions_json_path.write_text(json.dumps(emotions, ensure_ascii=False, indent=2), encoding="utf-8")
    azure.upload_file(emotions_json_path, emotions_blob)

    print("\nSaved to Azure:")
    try:
        print("Transcript:", azure.generate_sas_url(transcript_blob))
        print("Emotions:", azure.generate_sas_url(emotions_blob))
    except Exception:
        print(f"Uploaded blobs under: {run_dir}")


if __name__ == "__main__":
    test_emotion_analysis_end_to_end()



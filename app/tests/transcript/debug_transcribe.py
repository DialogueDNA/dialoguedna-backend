# app/tests/transcript/debug_transcribe.py
from pathlib import Path
import json

from app.services.transcript.transcriber import Transcriber
from app.storage.azure.blob.azure_blob_service import AzureBlobService

# ה-blob_path מההעלאה הקודמת
BLOB_AUDIO_PATH = "tests/angry_client_fixed/audio_file.wav"

# יעד ה-JSON ב-Azure
OUT_BLOB_JSON   = "tests/angry_client_fixed/transcript.json"

# נבנה שם קובץ מקומי לפי שם קובץ האודיו
AUDIO_STEM = Path(BLOB_AUDIO_PATH).stem  # angry_client_fixed
LOCAL_JSON = Path(__file__).parent / f"{AUDIO_STEM}_transcript.json"
TMP_JSON   = Path(__file__).parent / "_tmp_transcript.json"

def main():
    transcriber = Transcriber()
    blob = AzureBlobService()

    print(f"[debug] transcribing from blob: {BLOB_AUDIO_PATH}")
    lines = transcriber.transcribe(BLOB_AUDIO_PATH)

    print(f"[info] language={transcriber.transcript_language}, "
          f"duration_sec={transcriber.duration_seconds}, "
          f"speakers={transcriber.number_of_participants}")

    # כתיבה זמנית
    TMP_JSON.write_text(json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8")

    # עותק קבוע מקומי בשם דינמי
    LOCAL_JSON.write_text(json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] local transcript saved to: {LOCAL_JSON}")

    # העלאה ל-Azure
    blob.upload_file(TMP_JSON, OUT_BLOB_JSON)
    print(f"[OK] uploaded transcript JSON to: {OUT_BLOB_JSON}")

    try:
        TMP_JSON.unlink(missing_ok=True)
    except Exception:
        pass

if __name__ == "__main__":
    main()

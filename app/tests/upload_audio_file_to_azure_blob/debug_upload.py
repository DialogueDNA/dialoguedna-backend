# app/tests/transcript/debug_upload_direct.py
from pathlib import Path
from app.storage.azure.blob.azure_blob_service import AzureBlobService

def main():
    # נבנה נתיב יחסי לסקריפט הזה → ../audio/data/fixed/angry_client_fixed.wav
    here = Path(__file__).parent
    local_file = (here.parent / "audio" / "data" / "fixed" / "angry_client_fixed.wav").resolve()

    print(f"[debug] looking for: {local_file}")
    assert local_file.exists(), f"File not found: {local_file}"

    # יצירת השירות
    blob_service = AzureBlobService()

    # נגדיר לאן נעלה (ב־Azure זה יהיה tests/<שם הקובץ>/audio_file.wav)
    blob_path = f"tests/{local_file.stem}/audio_file.wav"

    # העלאה
    blob_service.upload_file(local_file, blob_path)

    print(f"[OK] Uploaded {local_file} to Azure at: {blob_path}")

if __name__ == "__main__":
    main()

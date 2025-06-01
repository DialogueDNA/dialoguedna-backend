from app.services.summarizer import Summarizer
from app.services.azure_uploader import AzureUploader
from app.core import config  # Load Azure keys and paths

def run_summary_generation():
    # Azure credentials
    connection_string = config.AZURE_STORAGE_CONNECTION_STRING
    container_name = config.AZURE_CONTAINER_NAME

    # Setup uploader and summarizer
    uploader = AzureUploader(connection_string=connection_string, container_name=container_name)
    summarizer = Summarizer()

    # 📥 Emotion JSON SAS URL (from emotion analysis stage)
    emotion_json_url = (
        "https://audiorecordstorage.blob.core.windows.net/sessions/0e139d18-0266-4be1-b569-c46b34c9af82/text_emotions.json"
        "?sp=rl&st=2025-05-31T21:25:30Z&se=2025-10-01T05:25:30Z&spr=https&sv=2024-11-04&sr=c"
        "&sig=XXXX_REPLACE_WITH_REAL_SIGNATURE"
    )

    # 👥 Speaker IDs (must match those used during transcription/emotion analysis)
    speaker_ids = ["0", "1"]
    session_id = "0e139d18-0266-4be1-b569-c46b34c9af82"

    # 🚀 Run summarization
    try:
        print("🚀 Starting summarization test...")
        summary_sas_url = summarizer.generate(emotion_json_url, speaker_ids, session_id)
        print("✅ Summary uploaded to:")
        print(summary_sas_url)
    except Exception as e:
        print("❌ Summarization failed:", str(e))


if __name__ == "__main__":
    run_summary_generation()

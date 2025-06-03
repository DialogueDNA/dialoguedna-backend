from app.services.archives.summarization.summarizer import Summarizer
from app.services.archives.infrastructure import AzureUploader
from app.core import config  # Load Azure keys and paths

def run_summary_generation():
    # Azure credentials
    connection_string = config.AZURE_STORAGE_CONNECTION_STRING
    container_name = config.AZURE_CONTAINER_NAME

    # Setup uploader and summarizer
    uploader = AzureUploader(connection_string=connection_string, container_name=container_name)
    summarizer = Summarizer()

    # 📥 Emotion JSON SAS URL (from emotion analysis stage)
    emotion_json_url = "https://audiorecordstorage.blob.core.windows.net/sessions/607c3aad-0d95-4f3e-8294-1e9d71d1cc19/emotion_analyzer.json?sp=r&st=2025-06-01T13:24:11Z&se=2025-06-01T21:24:11Z&spr=https&sv=2024-11-04&sr=b&sig=ZLsvCjC9aWtFZP%2BSJnUic3s%2BRH%2BrEZuwYGV2Fkre5HU%3D"



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

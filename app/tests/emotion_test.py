from app.services.archives.emotion_analysis.emotions_analysis_manager import EmotionsAnalysisManager
from app.services.archives.infrastructure import AzureUploader
from app.core import config

def run_emotion_analysis():
    # 🔐 Azure credentials from config
    connection_string = config.AZURE_STORAGE_CONNECTION_STRING
    container_name = config.AZURE_CONTAINER_NAME

    # ☁️ Setup uploader
    uploader = AzureUploader(connection_string=connection_string, container_name=container_name)

    # 🧠 Create emotion analysis manager
    analyzer = EmotionsAnalysisManager(uploader=uploader)

    # 📥 Transcription SAS URL (מהתמלול)
    transcript_sas_url = (
        "https://audiorecordstorage.blob.core.windows.net/sessions/0e139d18-0266-4be1-b569-c46b34c9af82/transcribe_with_diarization.txt"
        "?sp=rl&st=2025-05-31T21:25:30Z&se=2025-10-01T05:25:30Z&spr=https&sv=2024-11-04&sr=c"
        "&sig=XZa0EcDm55DSniz6bzWfhvOsZ4eFn4WmQ7p7ToH5RE4%3D"
    )

    # 🆔 session_id folder in Azure
    session_id = "0e139d18-0266-4be1-b569-c46b34c9af82"

    # 🚀 Run analysis
    try:
        print("🚀 Starting emotion analysis test...")
        result_sas_url = analyzer.analyze(transcript_sas_url, session_id)
        print("✅ Emotion result uploaded to:")
        print(result_sas_url)
    except Exception as e:
        print("❌ Emotion analysis failed:", str(e))

if __name__ == "__main__":
    run_emotion_analysis()

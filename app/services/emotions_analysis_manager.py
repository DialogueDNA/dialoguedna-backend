from app.core.config import TRANSCRIPTS_DIR, EMOTIONS_TEXT_DIR
from app.services.azure_uploader import AzureUploader
from app.services.emotion_analysis_text_manager import EmotionAnalysisTextManager
import tempfile
import requests
from pathlib import Path
from app.core.config import EMOTIONS_TEXT_DIR,AZURE_STORAGE_CONNECTION_STRING,AZURE_CONTAINER_NAME
from app.services.emotion_analysis_text_manager import EmotionAnalysisTextManager

class EmotionsAnalysisManager:
    def __init__(self, uploader: AzureUploader = None):
        self.uploader = uploader or AzureUploader(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )
        self.text_analyzer = None

        # # Find the transcript text file
        # transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
        # if not transcript_files:
        #     raise FileNotFoundError(f"No transcript .txt file found in {TRANSCRIPTS_DIR}")
        #
        # transcript_path = transcript_files[0]
        #
        # # Init the text-based emotion analyzer
        # self.text_analyzer = EmotionAnalysisTextManager(
        #     input_path=transcript_path,
        #     output_dir=EMOTIONS_TEXT_DIR
        # )
        # # self.tone_analyzer = EmotionAnalysisToneManager()  # ← add later

    def analyze(self, sas_url: str, session_id: str) -> tuple[str,str]:

        print("🧠 Starting emotion analysis...")

        # 🔽 Download the transcript file temporarily
        response = requests.get(sas_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download transcript: {response.status_code}")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(response.content)
        temp_file.close()

        # 🧠 Run emotion analysis
        self.text_analyzer = EmotionAnalysisTextManager(
            input_path=Path(temp_file.name),
            output_dir=EMOTIONS_TEXT_DIR,
            session_id=session_id
        )

        # Analyze from text
        text_result_path = self.text_analyzer.analyze()
        print(f"📄 Emotion analysis result saved at: {text_result_path}")

        # ☁️ Upload to Azure
        blob_name = f"{session_id}/emotion_analyzer.txt"
        print(f"☁️ Uploading emotion results to Azure as {blob_name}...")
        sas_url,blob_name = self.uploader.upload_file_and_get_sas(text_result_path, blob_name=blob_name)

        print("✅ Emotion analysis uploaded successfully.")
        return sas_url,blob_name



        # Future: Analyze from tone
        # tone_result_path = self.tone_analyzer.analyze()
        # print(f"🔊 Tone-based emotion result saved at: {tone_result_path}")

        # Future: Combine both results
        # merged_result = self.merge_results(text_result_path, tone_result_path)
        # return merged_result


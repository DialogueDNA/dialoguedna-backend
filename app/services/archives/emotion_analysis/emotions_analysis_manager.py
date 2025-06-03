from app.services.archives.infrastructure.azure_uploader import AzureUploader
from pathlib import Path
from app.core.config import AZURE_STORAGE_CONNECTION_STRING,AZURE_CONTAINER_NAME
from app.services.archives.emotion_analysis.emotion_analysis_text_manager import EmotionAnalysisTextManager


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

    def analyze(self, sas_url: str, session_id: str) -> dict:
        """
        Full emotion analysis pipeline:
        1. Downloads transcript from SAS URL
        2. Runs emotion analysis on it
        3. Saves emotion results to files (JSON and TXT)
        4. Uploads both files to Azure
        5. Returns dictionary with all info
        """
        import requests
        import tempfile

        print("🧠 Starting emotion analysis...")

        # 🔽 Download the transcript file temporarily
        response = requests.get(sas_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download transcript: {response.status_code}")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(response.content)
        temp_file.close()

        # 🧠 Run emotion analysis
        analyzer = EmotionAnalysisTextManager(
            input_path=Path(temp_file.name),
            output_dir=Path("app/conversation_session"),
            session_id=session_id
        )

        emotions_dict, json_path, txt_path = analyzer.analyze_and_return_all()

        # ☁️ Upload both results to Azure
        json_blob = f"{session_id}/text_emotions.json"
        txt_blob = f"{session_id}/text_emotions.txt"

        json_url,json_blob_name = self.uploader.upload_file_and_get_sas(json_path, blob_name=json_blob)
        txt_url,txt_blob_name = self.uploader.upload_file_and_get_sas(txt_path, blob_name=txt_blob)

        print("✅ Emotion analysis uploaded successfully.")

        return {
            "emotions_dict": emotions_dict,
            "json_url": json_url,
            "txt_url": txt_url,
            "json_blob_name": json_blob_name,
            "txt_blob_name": txt_blob_name
        }

    # def analyze(self, sas_url: str, session_id: str) -> str:
    #
    #     print("🧠 Starting emotion analysis...")
    #
    #     # 🔽 Download the transcript file temporarily
    #     response = requests.get(sas_url)
    #     if response.status_code != 200:
    #         raise Exception(f"Failed to download transcript: {response.status_code}")
    #
    #     temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    #     temp_file.write(response.content)
    #     temp_file.close()
    #
    #     # 🧠 Run emotion analysis
    #     self.text_analyzer = EmotionAnalysisTextManager(
    #         input_path=Path(temp_file.name),
    #         output_dir=EMOTIONS_TEXT_DIR,
    #         session_id=session_id
    #     )
    #
    #     # Analyze from text
    #     text_result_path = self.text_analyzer.analyze()
    #     print(f"📄 Emotion analysis result saved at: {text_result_path}")
    #
    #     # ☁️ Upload to Azure
    #     blob_name = f"{session_id}/emotion_analyzer.txt"
    #     print(f"☁️ Uploading emotion results to Azure as {blob_name}...")
    #     sas_url = self.uploader.upload_file_and_get_sas(text_result_path, blob_name=blob_name)
    #
    #     print("✅ Emotion analysis uploaded successfully.")
    #     return sas_url




        # Future: Analyze from tone
        # tone_result_path = self.tone_analyzer.analyze()
        # print(f"🔊 Tone-based emotion result saved at: {tone_result_path}")

        # Future: Combine both results
        # merged_result = self.merge_results(text_result_path, tone_result_path)
        # return merged_result


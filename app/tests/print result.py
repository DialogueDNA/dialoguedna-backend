import requests

def print_transcription_result(sas_url: str):
    print("📥 Downloading transcript from Azure...")
    response = requests.get(sas_url)

    if response.status_code == 200:
        print("✅ Transcript content:\n")
        print(response.text)
    else:
        print(f"❌ Failed to fetch transcript. Status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # 🟢 הדביקי כאן את ה-SAS URL המלא לקובץ
    transcript_sas_url = "https://audiorecordstorage.blob.core.windows.net/sessions/0e139d18-0266-4be1-b569-c46b34c9af82/transcribe_with_diarization.txt?se=2025-05-31T20%3A33%3A57Z&sp=r&sv=2025-05-05&sr=b&sig=7dsBbFc0U1ppayL1meNzrDcNuvWMTBt4wKaSmSzkn2M%3D"

    # 🚀 Call the function
    print_transcription_result(transcript_sas_url)

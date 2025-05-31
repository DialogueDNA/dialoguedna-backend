from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from pathlib import Path
import os
import uuid
from fastapi import UploadFile
from app.services.AudioConverter import AudioConverter

class AzureUploader:
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container = self.client.get_container_client(container_name)

    def upload_file_and_get_sas(self, file_path: Path) -> str:
        """
           Upload a file to Azure Blob Storage and generate a SAS URL for it.
           Prints status messages and errors to the console for debugging.
           """
        try:
            blob_name = file_path.name
            blob_client = self.container.get_blob_client(blob_name)

            print(f"☁️ Preparing to upload: {file_path}")

            # Open the file in binary mode and upload to Azure Blob Storage
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"✅ Upload completed: {blob_name}")

            # Generate a SAS URL for the uploaded blob
            sas_url = self._generate_sas_url(blob_name)
            print(f"🔗 SAS URL generated: {sas_url}")

            return sas_url

        except Exception as e:
            # Print the error to the console and raise a runtime error
            print(f"❌ Failed to upload or generate SAS URL: {str(e)}")
            raise RuntimeError(f"Upload failed: {str(e)}")

    def _generate_sas_url(self, blob_name: str, expiry_minutes: int = 60) -> str:
        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes)
        )
        url = f"https://{self.client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
        return url

    def convert_and_upload(self, input_path: Path, output_name: str = "original.wav") -> str:
        output_path = input_path.parent / output_name
        AudioConverter.convert_to_wav(str(input_path), str(output_path))
        return self.upload_file_and_get_sas(output_path)

def handle_upload_file(
    file: UploadFile,
    upload_folder: Path,
    uploader: AzureUploader
) -> str:
    """
    Save the uploaded file temporarily, convert it to WAV using its original filename,
    upload the converted file to Azure Blob Storage, and return the SAS URL.
    """
    # Ensure the upload folder exists
    os.makedirs(upload_folder, exist_ok=True)

    # Create a temporary unique filename for the uploaded file
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = upload_folder / temp_filename

    # Save the uploaded file to disk
    with open(temp_path, "wb") as f_out:
        f_out.write(file.file.read())

    # Use the original filename (but ensure it's WAV) for final upload
    original_filename = Path(file.filename).stem + ".wav"
    wav_path = upload_folder / original_filename

    # Convert to WAV format
    AudioConverter.convert_to_wav(str(temp_path), str(wav_path))

    # Upload the WAV file to Azure
    sas_url = uploader.upload_file_and_get_sas(wav_path)

    # Remove the temporary uploaded file
    os.remove(temp_path)

    return sas_url


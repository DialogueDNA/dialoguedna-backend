from typing import Union, IO
from pathlib import Path
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from pathlib import Path
from pydub import AudioSegment

class AzureUploader:
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container = self.client.get_container_client(container_name)

    def upload_file_and_get_sas(
        self,
        file_obj: Union[str, Path, IO[bytes]],
        blob_name: str,
        expiry_minutes: int = 60
    ) -> str:
        """
        Uploads a file to Azure Blob Storage and returns a SAS URL.
        Supports both file paths and file-like objects.
        """
        blob_client = self.container.get_blob_client(blob_name)

        if isinstance(file_obj, (str, Path)):
            with open(file_obj, "rb") as f:
                blob_client.upload_blob(f, overwrite=True)
        elif hasattr(file_obj, "read"):  # file-like object (e.g. UploadFile.file or BytesIO)
            blob_client.upload_blob(file_obj, overwrite=True)
        else:
            raise ValueError("file_obj must be a file path or file-like object")

        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self._get_account_key(),
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes)
        )

        return f"https://{self.client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

    def _get_account_key(self) -> str:
        for part in self.connection_string.split(";"):
            if part.startswith("AccountKey="):
                return part.split("=", 1)[1]
        raise ValueError("AccountKey not found in connection string")


    def convert_to_wav(self, input_path: Path) -> Path:
        """
        Converts any audio file to WAV format using pydub.
        Returns the path to the converted .wav file.
        """
        output_path = input_path.with_suffix(".wav")
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        return output_path
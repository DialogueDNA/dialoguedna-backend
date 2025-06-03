import os
from typing import Union, IO
from pathlib import Path
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from pathlib import Path
from pydub import AudioSegment

#___________________________________________#
from azure.storage.blob import BlobClient
from fastapi.responses import Response
from azure.storage.blob import BlobClient
import mimetypes
from typing import Tuple
#___________________________________________#


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
            expiry_hours: int = 24
    ) -> Tuple[str, str]:
        """
        Uploads a file to Azure Blob Storage and returns a tuple:
        (SAS URL for accessing the file, blob path where it was saved).
        Supports both file paths and file-like objects.
        """
        blob_client = self.container.get_blob_client(blob_name)

        if isinstance(file_obj, (str, Path)):
            with open(file_obj, "rb") as f:
                blob_client.upload_blob(f, overwrite=True)
        elif hasattr(file_obj, "read"):  # file-like object
            blob_client.upload_blob(file_obj, overwrite=True)
        else:
            raise ValueError("file_obj must be a file path or file-like object")

        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self._get_account_key(),
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )

        sas_url = f"https://{self.client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

        return sas_url, blob_name

    def _get_account_key(self) -> str:
        for part in self.connection_string.split(";"):
            if part.startswith("AccountKey="):
                return part.split("=", 1)[1]
        raise ValueError("AccountKey not found in connection string")

    def convert_to_wav(self, input_path: Path) -> Path:
        """
        Converts any audio file to WAV format with standard parameters for Azure STT.
        Ensures sample rate, format, and channel count are valid.
        """
        output_path = input_path.with_suffix(".wav")

        # Load the audio
        audio = AudioSegment.from_file(input_path)

        # Convert to mono and set sample rate to 16000Hz
        audio = audio.set_channels(1).set_frame_rate(16000)

        # Export with WAV format
        audio.export(output_path, format="wav")

        # Optional: check file size
        if os.path.getsize(output_path) < 1024:  # less than 1KB
            raise Exception("❌ Converted WAV file is too small – invalid audio")

        return output_path



    #-----------------------------------------------------------------------------------------#
    def get_file_response_from_azure_blob_storage(self, blob_name: str) -> Response:
        """
        Downloads a file from Azure Blob Storage and returns it as a FastAPI Response
        with the appropriate MIME type based on the file extension.
        """
        blob_client: BlobClient = self.container.get_blob_client(blob_name)

        if not blob_client.exists():
            raise FileNotFoundError(f"Blob '{blob_name}' not found in container '{self.container_name}'")

        content = blob_client.download_blob().readall()

        # Guess MIME type based on the file extension (e.g., .txt, .json, .wav)
        mime_type, _ = mimetypes.guess_type(blob_name)
        if mime_type is None:
            mime_type = "application/octet-stream"  # Fallback for unknown types

        return Response(content=content, media_type=mime_type)
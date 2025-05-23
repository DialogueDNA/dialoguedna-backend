from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from pathlib import Path
import os

class AzureUploader:
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container = self.client.get_container_client(container_name)

    def upload_file_and_get_sas(self, file_path: Path) -> str:
        """
        Upload the file to Azure Blob Storage and return a SAS URL.
        """
        blob_name = file_path.name
        blob_client = self.container.get_blob_client(blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        sas_url = self._generate_sas_url(blob_name)
        return sas_url

    def _generate_sas_url(self, blob_name: str, expiry_minutes: int = 60) -> str:
        """
        Generate a SAS URL for the uploaded blob.
        """
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

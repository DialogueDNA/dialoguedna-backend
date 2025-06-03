from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions,
)
from app.core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME


class AzureBlobFetcher:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container_name = AZURE_CONTAINER_NAME
        self.container = self.client.get_container_client(self.container_name)

    def generate_sas_url(self, blob_name: str, expiry_minutes: int = 60) -> str:
        """Generate a time-limited SAS URL for a blob."""
        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self._get_account_key(),
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
        )
        return f"https://{self.client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

    def blob_exists(self, blob_name: str) -> bool:
        """Check if a blob exists in Azure Blob Storage."""
        blob_client = self.container.get_blob_client(blob_name)
        try:
            blob_client.get_blob_properties()
            return True
        except Exception as e:
            print(f"⚠️ Unexpected error checking blob existence: {e}")
            return False

    def _get_account_key(self) -> str:
        """Extract the account key from the connection string."""
        for segment in AZURE_STORAGE_CONNECTION_STRING.split(";"):
            if segment.startswith("AccountKey="):
                return segment.replace("AccountKey=", "")
        raise ValueError("AccountKey not found in AZURE_STORAGE_CONNECTION_STRING")
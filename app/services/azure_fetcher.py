from datetime import datetime, timedelta

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

class AzureFetcher:
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container = self.client.get_container_client(container_name)

    def generate_sas_url(self, blob_name: str, expiry_minutes: int = 60) -> str:
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



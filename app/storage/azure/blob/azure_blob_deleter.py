from urllib.parse import urlparse
from azure.storage.blob import BlobServiceClient
from app.core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME


class AzureBlobDeleter:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container = self.client.get_container_client(AZURE_CONTAINER_NAME)

    def delete_blob(self, blob_name: str):
        """Delete a blob by name."""
        try:
            blob_client = self.container.get_blob_client(blob_name)
            blob_client.delete_blob()
        except Exception as e:
            print(f"⚠️ Failed to delete blob '{blob_name}': {e}")

    def delete_blob_from_url(self, url: str):
        """Delete a blob using its full URL (with or without SAS)."""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip("/").split("/", 1)
            if len(path_parts) != 2:
                raise ValueError(f"Invalid Azure blob URL: {url}")

            _, blob_path = path_parts
            blob_client = self.client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=blob_path)
            blob_client.delete_blob()
        except Exception as e:
            print(f"⚠️ Failed to delete blob from URL '{url}': {e}")
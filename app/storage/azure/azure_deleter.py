from azure.storage.blob import BlobClient, BlobServiceClient

from app.core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME

class AzureDeleter:

    def __init__(self):
        self.connection_string = AZURE_STORAGE_CONNECTION_STRING
        self.container_name = AZURE_CONTAINER_NAME
        self.client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        self.container = self.client.get_container_client(AZURE_CONTAINER_NAME)

    def delete_blob_from_url(self, url: str):
        try:
            blob_client = BlobClient.from_blob_url(blob_url=url)
            blob_client.delete_blob()
        except Exception as e:
            print(f"Failed to delete blob from URL: {url} — {e}")

    def delete_blob(self, blob_name: str):
        try:
            blob_client = self.container.get_blob_client(blob_name)
            blob_client.delete_blob()
        except Exception as e:
            print(f"Failed to delete blob '{blob_name}': {str(e)}")
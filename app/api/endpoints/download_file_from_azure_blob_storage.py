# main.py
from fastapi import FastAPI, Query, HTTPException
from azure_uploader import AzureUploader

app = FastAPI()

# Example: init uploader with your actual Azure config
azure_uploader = AzureUploader(
    connection_string="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net",
    container_name="your-container-name"
)

@app.get("/api/download_file_from_azure_blob_storage")
def get_file(path: str = Query(..., description="Blob path inside the container")):
    """
    Returns a file from Azure Blob Storage by its blob path.
    The file is streamed back with the correct Content-Type for the frontend.
    """
    try:
        return azure_uploader.get_file_response_from_azure_blob_storage(path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class AzureBlobConfig:
    connection_string: str = env.AZURE_BLOB_CONN_STR
    account_name: str = env.AZURE_BLOB_ACCOUNT
    account_key: str = env.AZURE_BLOB_KEY
    public_base_url: str = env.AZURE_BLOB_PUBLIC_BASE

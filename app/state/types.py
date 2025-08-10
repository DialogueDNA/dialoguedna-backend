# app/state/types.py
from dataclasses import dataclass, field
from typing import Optional, Protocol, Any, Callable, Dict

from app.db.registry import GatewayRegistry
from app.ports.db.table_gateway import TableGateway
from app.ports.storage.blob_storage import BlobStorage
from app.ports.db.domains.users_repo import UsersRepo
from app.ports.db.domains.sessions_repo import SessionsRepo


# ---- DB ----
TableGatewayFactory = Callable[[str], TableGateway]

@dataclass
class DBState:
    gateway_registry: Optional[GatewayRegistry] = None
    users_repo: Optional[UsersRepo] = None
    sessions_repo: Optional[SessionsRepo] = None

# ---- Storage ----
@dataclass
class StorageState:
    client: Optional[BlobStorage] = None
    azure_blob_service: Optional[Any] = None
    _azure_account_key: Optional[str] = None

# ---- Services ----
# @dataclass
# class ServicesState:
#     transcriber: Optional[Any] = None

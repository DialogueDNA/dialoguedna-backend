# app/storage/adapters/local/local_fs.py
from __future__ import annotations
from pathlib import Path
from typing import BinaryIO
from app.ports.storage.blob_storage import BlobStorage

class LocalFSAdapter(BlobStorage):
    def __init__(self, root: str):
        self.root = Path(root)

    def _path(self, container: str, blob: str) -> Path:
        return self.root / container / blob

    def upload(self, container: str, blob: str, data: bytes | BinaryIO, *, content_type: str | None = None) -> str:
        p = self._path(container, blob)
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (bytes, bytearray)):
            content = data
        else:
            content = data.read()
        p.write_bytes(content)
        return self.url(container, blob)

    def download(self, container: str, blob: str) -> bytes:
        return self._path(container, blob).read_bytes()

    def delete(self, container: str, blob: str) -> None:
        p = self._path(container, blob)
        if p.exists():
            p.unlink()

    def url(self, container: str, blob: str, *, public: bool = False) -> str:
        # מסלול קובץ מקומי (לשרת). בפרודקשן עדיף להגיש דרך CDN/Static.
        return self._path(container, blob).as_uri()

    def generate_sas_url(self, container: str, blob: str, *, expiry_seconds: int = 3600) -> str:
        # אין SAS בלוקלי—נחזיר פשוט את ה-URL
        return self.url(container, blob)
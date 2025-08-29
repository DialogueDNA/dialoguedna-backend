from __future__ import annotations

import gzip
import inspect
import json
import mimetypes
import os
import tempfile
from typing import Any, Mapping, Optional, Dict, List, TypeVar, Type

from app.interfaces.storage.blob_storage import BlobStorage
from app.logic.DialogueDNA.interfaces.capabilities import SessionUpdater, ArtifactWriter

# Wrap a repo to expose only "update"
class RepoSessionUpdater(SessionUpdater):
    def __init__(self, sessions_repo):
        self._repo = sessions_repo
    def update(self, session_id: str, updates: Mapping[str, Any]) -> Any:
        return self._repo.update(session_id, dict(updates))


class StorageArtifactWriter(ArtifactWriter):
    def __init__(self, blob_storage: BlobStorage):
        self.blob_storage = blob_storage

    def put_json_get_url(self, container: str, blob: str, some_json: List[Dict[str, Any]]) -> Optional[str]:
        data = json.dumps(some_json, ensure_ascii=False).encode("utf-8")
        self.blob_storage.upload(container=container, blob=blob, data=data)
        return None

    def put_wav_path_get_url(self, container: str, blob: str, some_wav_path: str) -> Optional[str]:
        """
        Upload a local WAV (or other audio) file to storage and return a canonical URL if available.
        Uses the BlobStorage.upload(container, blob, data=...) contract.
        """
        # Guess MIME from file extension; default to audio/wav
        guessed = mimetypes.guess_type(some_wav_path)[0]
        content_type = guessed or "audio/wav"

        # Read file bytes (simple & compatible). If your BlobStorage supports streaming,
        # you can extend this to pass a file-like object instead.
        with open(some_wav_path, "rb") as f:
            data = f.read()

        # Try passing content_type if the upload() signature supports it; fall back otherwise.
        try:
            result = self.blob_storage.upload(
                container=container,
                blob=blob,
                data=data,
                content_type=content_type,
            )
        except TypeError:
            # Wrapper doesn't accept content_type
            result = self.blob_storage.upload(container=container, blob=blob, data=data)

        # If upload() returns a URL, use it.
        if isinstance(result, str) and result.startswith("http"):
            return result

        # If no URL mechanism exists, return None (caller can resolve later if needed).
        return None



T = TypeVar("T")
class StorageArtifactReader:
    """
    Opposite of put_json_get_url: fetch JSON from blob storage and
    construct Python objects.
    """
    def __init__(self, blob_storage):
        self.blob_storage = blob_storage  # must expose .download(container, blob) -> bytes

    def _download_json(self, container: str, blob: str) -> List[Dict[str, Any]]:
        data: bytes = self.blob_storage.download(container=container, blob=blob)
        text = data.decode("utf-8")
        obj = json.loads(text)

        if isinstance(obj, list):
            items = [x for x in obj if isinstance(x, dict)]
            if not items:
                raise ValueError(f"{container}/{blob}: JSON array contains no objects")
            return items

        if isinstance(obj, dict):
            return [obj]

        raise ValueError(f"{container}/{blob}: Expected JSON object or array of objects")

    def _download_audio(self, container: str, blob: str, out_path="/") -> str:

        audio_bytes: bytes = self.blob_storage.download(
            container=container,
            blob=blob,
        )

        # Decompress if gzip (magic bytes: 1F 8B)
        if len(audio_bytes) >= 2 and audio_bytes[0] == 0x1F and audio_bytes[1] == 0x8B:
            audio_bytes = gzip.decompress(audio_bytes)

        # Choose output path
        if out_path is None:
            fd, tmp = tempfile.mkstemp(suffix=".wav", prefix="audio_", text=False)
            os.close(fd)  # we'll reopen below
            out_path = tmp
        elif not out_path.lower().endswith(".wav"):
            out_path = f"{out_path}.wav"

        # Write bytes to disk
        with open(out_path, "wb") as f:
            f.write(audio_bytes)

        return out_path

    @staticmethod
    def _construct(cls: Type[T], payload: Dict[str, Any]) -> T:
        """
        Safely construct cls(**kwargs) ignoring extra keys.
        """
        params = set(inspect.signature(cls).parameters.keys())
        filtered = {k: v for k, v in payload.items() if k in params}
        return cls(**filtered)  # type: ignore[arg-type]

    def load_many(self, container: str, blob: str, cls: Type[T]) -> List[T]:
        """
        For files like transcript.json / emotions.json (arrays).
        """
        items = self._download_json(container, blob)
        return [self._construct(cls, d) for d in items]

    def load_one(self, container: str, blob: str, cls: Type[T]) -> T:
        """
        For files like summary.json (single object or array with one object).
        """
        items = self._download_json(container, blob)
        if len(items) != 1:
            raise ValueError(f"{container}/{blob}: expected single object, got {len(items)}")
        return self._construct(cls, items[0])

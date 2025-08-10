# app/settings/config.py
from __future__ import annotations
import os
from dataclasses import dataclass
import logging
import torch
import app.settings.environment as env

log = logging.getLogger("app.config")

# === DB ===
@dataclass(frozen=True)
class DBConfig:
    domain_backends: dict[str, str] = None

    supabase_url: str = env.SUPABASE_URL
    supabase_key: str = env.SUPABASE_SERVICE_ROLE_KEY

    def __post_init__(self):
        if self.domain_backends is None:
            object.__setattr__(self, "domain_backends", {
                "users": env.USERS_DB_BACKEND,
                "sessions": env.SESSIONS_DB_BACKEND,
            })

    @property
    def backends_in_use(self) -> set[str]:
        return set(self.domain_backends.values())

# === Storage ===
@dataclass(frozen=True)
class StorageConfig:
    backend: str = env.STORAGE_BACKEND
    azure_conn_str: str = env.AZURE_BLOB_CONN_STR
    azure_account: str = env.AZURE_BLOB_ACCOUNT
    azure_key: str = env.AZURE_BLOB_KEY
    azure_public_base: str = env.AZURE_BLOB_PUBLIC_BASE
    local_root: str = env.LOCAL_STORAGE_ROOT

# === AppConfig ===
@dataclass(frozen=True)
class AppConfig:
    db: DBConfig = DBConfig()
    storage: StorageConfig = StorageConfig()

def _detect_device() -> str:
    if d := os.getenv("DEVICE"):
        return d
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"

def _gpu_mem_gb() -> float | None:
    if torch.cuda.is_available():
        try:
            return torch.cuda.get_device_properties(0).total_memory / 1024**3
        except Exception as e:
            log.warning("Failed to read GPU memory: %s", e)
    return None

@dataclass(frozen=True)
class WhisperXConfig:
    model_size: str = os.getenv("WHISPERX_MODEL_SIZE", "large-v2")
    batch_size: int = 4
    compute_type: str = os.getenv("WHISPERX_COMPUTE_TYPE", "int8")
    device: str = _detect_device()

    @staticmethod
    def autotune() -> "WhisperXConfig":
        device = _detect_device()
        batch = 4
        compute = "int8"
        if device == "cuda":
            mem = _gpu_mem_gb() or 0.0
            log.info("[Config] GPU memory detected: %.1f GB", mem)
            compute = "float16" if mem >= 8 else "int8_float16"
            if mem >= 24:
                batch = 24
            elif mem >= 16:
                batch = 16
            elif mem >= 8:
                batch = 8
        else:
            log.info("[Config] No CUDA GPU detected (device=%s). Using CPU/MPS defaults.", device)
        log.info("[Config] DEVICE=%s, BATCH_SIZE=%d, COMPUTE_TYPE=%s", device, batch, compute)
        return WhisperXConfig(batch_size=batch, compute_type=compute, device=device)
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional

import app.core.environment as env

@dataclass(frozen=True)
class JHartmannConfig:
    """
    Config for text-based emotion classification using a Hugging Face model.

    Fields:
      - model: Hugging Face hub id or local path to an emotion classifier.
               Good default: "j-hartmann/emotion-english-distilroberta-base".
      - device: HF pipeline device index (e.g., -1=CPU, 0=CUDA:0).
      - top_k: If None -> return scores for ALL labels; otherwise return top-k labels.
      - cache_dir: where to store downloaded model files.
    """
    model: str = env.J_HARTMANN_MODEL_NAME
    device: int = env.DEVICE
    top_k: Optional[int] = env.J_HARTMANN_TOP_K
    cache_dir: str = field(
        default_factory=lambda: os.path.join(
            os.path.expanduser("~"), ".cache", "hf", "emotion-text"
        )
    )

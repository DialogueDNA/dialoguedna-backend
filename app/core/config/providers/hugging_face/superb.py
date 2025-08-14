import os
from dataclasses import dataclass, field

import app.core.environment as env

@dataclass(frozen=True)
class SuperbConfig:
    """
    Configuration for the HF-based audio emotion analyzer.

    - model: HF hub id or local path for an *audio* classification checkpoint.
             Good defaults: "superb/hubert-large-superb-er",
             "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition".
    - device: "cpu" or "cuda" (optionally "cuda:0", etc.).
    - cache_dir: where model files are stored.
    - window_sec / hop_fraction: sliding-window params for long audio.
    """
    model: str = env.SEPFORMER_MODEL_NAME
    device: str = env.DEVICE
    cache_dir: str = field(
        default_factory=lambda: os.path.join(os.path.expanduser("~"), ".cache", "hf", "emotion-audio"))
    window_sec: float = 6.0
    hop_fraction: float = 0.5
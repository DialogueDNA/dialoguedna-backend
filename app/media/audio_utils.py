# app/media/audio_utils.py
# Purpose: guarantee Azure-friendly audio (WAV, PCM s16, 16 kHz, mono)
# Dependencies: pydub (with ffmpeg/avconv installed)

from __future__ import annotations
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

from pydub import AudioSegment

# Read target settings from central config
from app.core.config import (
    SAMPLE_RATE,        # 16000
    TARGET_CHANNELS,    # 1
    TARGET_BIT_DEPTH,   # 16 (=> 2 bytes)
    TARGET_CONTAINER,   # "wav"
    TARGET_CODEC,       # "pcm_s16le" (informational)
)

# --------------------------- Public API ---------------------------

def ensure_transcription_ready(src_path: Path) -> Path:
    """
    Ensure the file at `src_path` is WAV, PCM s16, 16 kHz, mono.
    If it already matches, returns the original path.
    Otherwise, creates a converted temp WAV and returns its path.
    """
    src_path = Path(src_path)

    if _is_wav_pcm16_mono16k(src_path):
        return src_path

    # Load with pydub (decodes via ffmpeg)
    audio = AudioSegment.from_file(src_path)

    # Enforce 16kHz / mono / 16-bit PCM
    audio = (
        audio.set_frame_rate(int(SAMPLE_RATE))
             .set_channels(int(TARGET_CHANNELS))
             .set_sample_width(int(TARGET_BIT_DEPTH // 8))
    )

    # Export to a temp WAV file (PCM s16le is default for pydub WAV with sample_width=2)
    with NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp_path = Path(tmp.name)

    audio.export(tmp_path, format=TARGET_CONTAINER)

    return tmp_path


def probe(path: Path) -> Dict[str, object]:
    """
    Return basic audio properties for logging/verification.
    NOTE: 'codec' is best-effort; pydub doesn't expose the exact codec,
    so we infer PCM s16 if WAV+16-bit sample width.
    """
    path = Path(path)
    audio = AudioSegment.from_file(path)

    sample_rate = audio.frame_rate
    channels = audio.channels
    bit_depth = audio.sample_width * 8
    duration_sec = len(audio) / 1000.0
    container = path.suffix.lstrip(".").lower()

    if container == "wav" and bit_depth == 16:
        codec = "pcm_s16le"
    else:
        codec = "unknown"

    return {
        "sample_rate": sample_rate,
        "channels": channels,
        "bit_depth": bit_depth,
        "duration_sec": duration_sec,
        "container": container,
        "codec": codec,
    }

# -------------------------- Internal helpers --------------------------

def _is_wav_pcm16_mono16k(path: Path) -> bool:
    """
    Quick check: WAV container, 16-bit, mono, 16 kHz.
    """
    try:
        path = Path(path)
        if path.suffix.lower() != ".wav":
            return False

        audio = AudioSegment.from_file(path)
        return (
            audio.frame_rate == int(SAMPLE_RATE) and
            audio.channels == int(TARGET_CHANNELS) and
            audio.sample_width == int(TARGET_BIT_DEPTH // 8)
        )
    except Exception:
        return False

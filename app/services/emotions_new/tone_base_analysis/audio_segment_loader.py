# Path: app/services/emotions_new/tone_base_analysis/audio_segment_loader.py
# Purpose: Load/cut audio by start/end and return (samples, sample_rate, duration_sec, qc).
# Notes: Dummy mode returns None samples (still useful for wiring and duration-based rules).
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple, Union

try:
    import numpy as np  # optional
except Exception:
    np = None  # type: ignore


class AudioSegmentLoader:
    def __init__(self, target_sr: int = 16000, use_dummy: bool = True) -> None:
        self.target_sr = int(target_sr)
        self.use_dummy = bool(use_dummy)

    def load(
        self,
        wav_path: Union[str, Path],
        start_time: float,
        end_time: float,
    ) -> Tuple[Any, int, float, Dict[str, Any]]:
        start_time = float(start_time)
        end_time = float(end_time)
        duration = max(0.0, end_time - start_time)

        if self.use_dummy:
            qc = {"is_short": duration < 0.7, "silence_ratio": None, "snr_db": None}
            return None, self.target_sr, duration, qc

        # Try soundfile for accurate slicing
        try:
            import soundfile as sf  # type: ignore
            with sf.SoundFile(str(wav_path), "r") as f:
                sr = int(f.samplerate)
                s = max(0, int(start_time * sr))
                e = max(s, int(end_time * sr))
                f.seek(s)
                frames = e - s
                data = f.read(frames, dtype="float32", always_2d=True)  # (frames, channels)

            if np is not None:
                mono = data.mean(axis=1).astype("float32")
                duration = len(mono) / sr if sr else duration
                qc = {
                    "is_short": duration < 0.7,
                    "silence_ratio": float((np.abs(mono) < 1e-3).mean()) if len(mono) else 1.0,
                    "snr_db": None,
                }
                return mono, sr, duration, qc
            else:
                mono = [float(sum(frame) / len(frame)) for frame in data]  # type: ignore
                dur = (len(mono) / sr) if sr else duration
                qc = {"is_short": dur < 0.7, "silence_ratio": None, "snr_db": None}
                return mono, sr, dur, qc
        except Exception:
            # Fallback: just report duration & nominal SR
            try:
                import wave
                with wave.open(str(wav_path), "rb") as w:
                    sr = w.getframerate()
            except Exception:
                sr = self.target_sr
            qc = {"is_short": duration < 0.7, "silence_ratio": None, "snr_db": None}
            return None, int(sr), duration, qc

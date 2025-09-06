# Purpose: Load/cut audio by start/end and return (samples, sample_rate, duration_sec, qc).
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple, Union


import numpy as np
from pydub import AudioSegment

class AudioSegmentLoader:
    def __init__(self, target_sr: int = 16000, use_dummy: bool = False) -> None:
        self.target_sr = int(target_sr)
        self.use_dummy = bool(use_dummy)

    def load(
        self,
        wav_path: Union[str, Path],   # כאן זה ה-local_src המקורי
        start_time: float,
        end_time: float,
    ) -> Tuple[np.ndarray, int, float, Dict[str, Any]]:
        start_time = float(start_time)
        end_time = float(end_time)
        if end_time < start_time:
            end_time = start_time

        # טוען מקור גולמי מכל פורמט, וחותך לפי מילישניות
        src = str(wav_path)
        audio = AudioSegment.from_file(src)

        start_ms = max(0, int(start_time * 1000))
        end_ms = max(start_ms, int(end_time * 1000))
        seg = audio[start_ms:end_ms]

        # הבטחת מינימום קטע קצר אם נחתך לריק (מקרה גבול)
        if len(seg) == 0:
            seg = AudioSegment.silent(duration=100, frame_rate=audio.frame_rate)

        # מייצב ל-16kHz מונו, 16bit PCM
        seg = seg.set_frame_rate(self.target_sr).set_channels(1).set_sample_width(2)

        # המרה ל-numpy float32 בטווח [-1, 1]
        arr = np.frombuffer(seg.raw_data, dtype=np.int16)
        samples = (arr.astype(np.float32) / 32768.0)
        sr = self.target_sr
        duration = float(len(samples) / sr) if sr and len(samples) else 0.0
        silence_ratio = float((np.abs(samples) < 1e-3).mean()) if len(samples) else 1.0

        qc = {"is_short": duration < 0.7, "silence_ratio": silence_ratio, "snr_db": None}
        return samples, sr, duration, qc


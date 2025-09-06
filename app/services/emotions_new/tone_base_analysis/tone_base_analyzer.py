# Path: app/services/emotions_new/tone_base_analysis/tone_base_analyzer.py
# Purpose: Run tone-based emotion analysis per sentence and return 4-class probs (+neutral).
# Output shape (per sentence):
#   {
#     "speaker": "...",
#     "start_time": float, "end_time": float,
#     "emotions4": [  # EMOTIONS_4 order, sorted desc
#       {"label":"angry","score":...},
#       {"label":"happy","score":...},
#       {"label":"sad","score":...},
#       {"label":"neutral","score":...}
#     ],
#     "confidence": float,  # top - second (or use 1-entropy if you prefer)
#     "qc": {"duration_sec": float, "is_backchannel": bool, ...}
#   }
from __future__ import annotations
from typing import Tuple

from typing import Any, Dict, List, Union

from .audio_segment_loader import AudioSegmentLoader
from .backchannel import detect as detect_backchannel

from urllib.parse import urlparse
from pathlib import Path
from hashlib import md5
import requests
from pydub import AudioSegment


EMOTIONS_4 = ["angry", "happy", "sad", "neutral"]
_HF2API = {"ang": "angry", "hap": "happy", "sad": "sad", "neu": "neutral"}



class ToneBaseAnalyzer:
    def __init__(
        self,
        model_id: str = "superb/hubert-large-superb-er",
        device: str | None = None,
        loader: AudioSegmentLoader | None = None,
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.loader = loader or AudioSegmentLoader()
        self._model = None  # lazy real model (HF pipeline) if/when needed

    def analyze(
            self,
            audio_blob_path: Union[str, Path],
            transcript_json: Dict[str, Any],
            local_src : Union[str, Path]
    ) -> Dict[str, Any]:
        sentences = list(transcript_json.get("utterances", []))
        out: List[Dict[str, Any]] = []

        try:
            for s in sentences:
                speaker = str(s.get("speaker", "?")).strip()
                text = str(s.get("text", "")).strip()
                start = float(s.get("start_time", 0.0))
                end = float(s.get("end_time", start))

                # 1) cut/load audio
                samples, sr, duration_sec, qc = self.loader.load(local_src, start, end)

                # 2) infer 4-class probs
                probs4 = self._infer_probs4(samples, sr)

                # 3) meta/qc
                is_back = detect_backchannel(text, duration_sec)
                qc_out = {"duration_sec": float(duration_sec), "is_backchannel": bool(is_back), **qc}

                # 4) package
                emotions4 = self._to_api_list(probs4)
                conf = self._confidence_margin(probs4)

                out.append({
                    "speaker": speaker,
                    "start_time": start,
                    "end_time": end,
                    "emotions4": emotions4,
                    "confidence": conf,
                    "qc": qc_out,
                })
            return {"utterances": out}
        finally:
            try:
                local_src.unlink(missing_ok=True)  # דורש Python 3.8+
            except Exception:
                pass


    # ---- internals ----
    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        from transformers import pipeline  # import here to avoid import cost at module load
        kwargs: Dict[str, Any] = dict(
            task="audio-classification",
            model=self.model_id,
            #return_all_scores=True,
        )
        if self.device is not None:
            kwargs["device"] = self.device
        self._model = pipeline(**kwargs)
        # )

    def _infer_probs4(self, samples, sample_rate: int) -> List[float]:
        """Return probabilities in EMOTIONS_4 order using the real HF pipeline."""
        if samples is None or sample_rate is None:
            raise RuntimeError("No audio samples provided to emotion model.")
        self._ensure_model()

        out = self._model({"array": samples, "sampling_rate": int(sample_rate)}, top_k=None)
        # out is a list of dicts: [{'label':'neu','score':...}, ...]
        items = out if isinstance(out, list) else [out]
        by = {str(it["label"]).lower(): float(it["score"]) for it in items}

        # Map HF labels to API order
        angry = by.get("ang", 0.0)
        happy = by.get("hap", 0.0)
        sad = by.get("sad", 0.0)
        neutral = by.get("neu", 0.0)
        return [angry, happy, sad, neutral]

    def _confidence_margin(self, probs4: List[float]) -> float:
        xs = sorted([float(p) for p in probs4], reverse=True)
        if not xs:
            return 0.0
        if len(xs) == 1:
            return xs[0]
        return max(0.0, xs[0] - xs[1])

    def _to_api_list(self, probs4: List[float]) -> List[Dict[str, float]]:
        pairs = [{"label": lbl, "score": float(p)} for lbl, p in zip(EMOTIONS_4, probs4)]
        pairs.sort(key=lambda x: x["score"], reverse=True)
        return pairs


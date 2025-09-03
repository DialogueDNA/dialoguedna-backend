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

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from .audio_segment_loader import AudioSegmentLoader
from .backchannel import detect as detect_backchannel

EMOTIONS_4 = ["angry", "happy", "sad", "neutral"]


class ToneBaseAnalyzer:
    def __init__(
        self,
        model_id: str = "superb/hubert-large-superb-er",
        device: str | None = None,
        loader: AudioSegmentLoader | None = None,
        use_dummy: bool = True,    # flip to False when wiring the real model
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.loader = loader or AudioSegmentLoader()
        self.use_dummy = use_dummy
        self._model = None  # lazy real model (HF pipeline) if/when needed

    def analyze(
        self,
        audio_blob_path: Union[str, Path],
        transcript_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        wav_path = Path(audio_blob_path)
        sentences = list(transcript_json.get("utterances", []))  # keep key name for compatibility

        out: List[Dict[str, Any]] = []
        for s in sentences:
            speaker = str(s.get("speaker", "?")).strip()
            text = str(s.get("text", "")).strip()
            start = float(s.get("start_time", 0.0))
            end = float(s.get("end_time", start))

            # 1) cut/load audio
            samples, sr, duration_sec, qc = self.loader.load(wav_path, start, end)

            # 2) infer 4-class probs
            probs4 = self._infer_probs4(samples, sr)

            # 3) meta/qc
            is_back = detect_backchannel(text, duration_sec)
            qc_out = {"duration_sec": float(duration_sec), "is_backchannel": bool(is_back), **qc}

            # 4) package as emotions4 (sorted desc) + confidence
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

    # ---- internals ----
    def _ensure_model(self) -> None:
        if self._model is not None or self.use_dummy:
            return
        # from transformers import pipeline
        # self._model = pipeline(
        #     task="audio-classification",
        #     model=self.model_id,
        #     device=self.device,
        #     return_all_scores=True,
        # )

    def _infer_probs4(self, samples, sample_rate: int) -> List[float]:
        """Return probabilities in EMOTIONS_4 order. Dummy mode = safe placeholder."""
        if self.use_dummy:
            # simple placeholder: short → more neutral
            dur = 0.0 if samples is None or not sample_rate else len(samples) / float(sample_rate)
            bias = 0.0 if dur >= 0.7 else 0.4
            angry = 0.22 * (1.0 - bias)
            happy = 0.24 * (1.0 - bias)
            sad = 0.18 * (1.0 - bias)
            neutral = 1.0 - (angry + happy + sad)
            return [float(angry), float(happy), float(sad), float(max(0.0, neutral))]

        self._ensure_model()
        # Example real call (when wired):
        # out = self._model({"array": samples, "sampling_rate": sample_rate})
        # items = out if isinstance(out, list) else [out]
        # by = {str(it["label"]).lower(): float(it["score"]) for it in items}
        # return [float(by.get(lbl, 0.0)) for lbl in EMOTIONS_4]
        return [0.1, 0.1, 0.1, 0.7]  # neutral-ish fallback

    def _confidence_margin(self, probs4: List[float]) -> float:
        """Top-2 margin as a simple confidence proxy."""
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

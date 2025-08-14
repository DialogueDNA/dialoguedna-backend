from __future__ import annotations
from typing import Dict, List, Tuple, Optional

from app.ports.services.emotions.audio_emotioner import AudioSegmentOutput
from app.ports.services.emotions.fusion_emotioner import SpeakerT, FusionSegmentOutput
from app.ports.services.emotions.text_emotioner import TextSegmentOutput


def _norm_label(lab: str) -> str:
    return lab.strip().lower().replace(" ", "_")

def _key(speaker: SpeakerT, st: float, et: float, txt: str, nd: int) -> Tuple[SpeakerT, float, float, str]:
    return speaker, round(float(st), nd), round(float(et), nd), txt or ""

def _weighted_merge(a: Dict[str, float], b: Dict[str, float], wa: float, wb: float, renorm: bool=True) -> Dict[str, float]:
    out: Dict[str, float] = {}
    a = {_norm_label(k): v for k, v in a.items()}
    b = {_norm_label(k): v for k, v in b.items()}
    labels = set(a) | set(b)
    for k in labels:
        out[k] = a.get(k, 0.0) * wa + b.get(k, 0.0) * wb
    if renorm:
        s = sum(out.values())
        if s > 0:
            for k in list(out.keys()):
                out[k] = out[k] / s
    return out


class EmotionFusionByWeights:
    """
    Weight-based fusion of text & audio emotion predictions. No model here.
    """
    def __init__(self, audio_weight: float = 0.6, text_weight: float = 0.4, time_decimals: int = 3, renorm: bool = True):
        if audio_weight < 0 or text_weight < 0 or (audio_weight + text_weight) == 0:
            raise ValueError("Invalid fusion weights.")
        s = audio_weight + text_weight
        self.wa = audio_weight / s
        self.wt = text_weight / s
        self.nd = time_decimals
        self.renorm = renorm

    def fuse(self, text_results: List[TextSegmentOutput], audio_results: List[AudioSegmentOutput]) -> List[FusionSegmentOutput]:
        fused: Dict[Tuple[SpeakerT, float, float, str], FusionSegmentOutput] = {}

        # Seed text side
        for t in text_results:
            k = _key(t["speaker"], t["start_time"], t["end_time"], t.get("text", ""), self.nd)
            fused[k] = {
                "speaker": t["speaker"],
                "text": t.get("text", ""),
                "start_time": round(float(t["start_time"]), self.nd),
                "end_time": round(float(t["end_time"]), self.nd),
                "emotions": dict(t.get("emotions", {}))
            }

        # Merge audio
        for a in audio_results:
            # match by (speaker, times) ignoring text
            mk: Optional[Tuple[SpeakerT, float, float, str]] = None
            for k in fused.keys():
                if k[0] == a["speaker"] and k[1] == round(float(a["start_time"]), self.nd) and k[2] == round(float(a["end_time"]), self.nd):
                    mk = k
                    break
            if mk is None:
                k = _key(a["speaker"], a["start_time"], a["end_time"], "", self.nd)
                fused[k] = {
                    "speaker": a["speaker"],
                    "text": "",
                    "start_time": round(float(a["start_time"]), self.nd),
                    "end_time": round(float(a["end_time"]), self.nd),
                    "emotions": _weighted_merge({}, a.get("emotions", {}), self.wt, self.wa, self.renorm)
                }
            else:
                fused[mk]["emotions"] = _weighted_merge(
                    fused[mk]["emotions"],
                    a.get("emotions", {}),
                    self.wt, self.wa, self.renorm
                )

        out = list(fused.values())
        out.sort(key=lambda r: (r["start_time"], str(r["speaker"])))
        return out
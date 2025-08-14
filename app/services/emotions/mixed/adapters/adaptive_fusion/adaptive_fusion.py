from __future__ import annotations
from typing import Dict, List, Tuple, Union, Optional
import math

from app.ports.services.emotions.audio_emotioner import AudioSegmentOutput
from app.ports.services.emotions.fusion_emotioner import FusionSegmentOutput
from app.ports.services.emotions.text_emotioner import TextSegmentOutput

SpeakerT = Union[str, int]

def _norm(l: str) -> str:
    return l.strip().lower().replace(" ", "_")

def _key(s: SpeakerT, st: float, et: float, txt: str, nd: int) -> Tuple[SpeakerT, float, float, str]:
    return (s, round(float(st), nd), round(float(et), nd), txt or "")

def _softmax2(a: float, b: float) -> tuple[float, float]:
    ea, eb = math.exp(a), math.exp(b)
    s = ea + eb
    return ea / s, eb / s

class EmotionFusionByAdaptive:
    """
    Adaptive fusion: compute per-segment weights based on simple quality features.
    Falls back to fixed weights if features are missing.
    """
    def __init__(
        self,
        base_audio_w: float = 0.6,
        base_text_w: float = 0.4,
        time_decimals: int = 3,
        renorm: bool = True,
        # coefficients for logit scoring
        a_bias: float = 0.0, a_snr: float = 0.08, a_dur: float = 0.02, a_overlap: float = -0.8,
        t_bias: float = 0.0, t_conf: float = 1.2, t_len: float = 0.03
    ):
        s = base_audio_w + base_text_w
        self.baw = base_audio_w / s
        self.btw = base_text_w / s
        self.nd = time_decimals
        self.renorm = renorm
        # coefficients
        self.a_bias, self.a_snr, self.a_dur, self.a_overlap = a_bias, a_snr, a_dur, a_overlap
        self.t_bias, self.t_conf, self.t_len = t_bias, t_conf, t_len

    def _infer_weights(self, tmeta: Optional[Dict[str, float]], ameta: Optional[Dict[str, float]]) -> tuple[float, float]:
        """
        Produce (w_text, w_audio) between 0..1 that sum to 1 using a tiny 2-logit model.
        Features (optional):
          - ameta: snr (dB), duration (sec), overlap (0/1)
          - tmeta: asr_conf (0..1), num_words (int)
        """
        # Start with base logits from base weights
        # Convert base weights to pseudo-logits
        ba = math.log(max(self.baw, 1e-6)); bt = math.log(max(self.btw, 1e-6))
        # audio logit
        a_logit = ba + self.a_bias
        if ameta:
            a_logit += self.a_snr * float(ameta.get("snr", 0.0))
            a_logit += self.a_dur * float(ameta.get("duration", 0.0))
            a_logit += self.a_overlap * float(ameta.get("overlap", 0.0))
        # text logit
        t_logit = bt + self.t_bias
        if tmeta:
            t_logit += self.t_conf * float(tmeta.get("asr_conf", 0.0))
            t_logit += self.t_len * float(tmeta.get("num_words", 0.0))
        wt, wa = _softmax2(t_logit, a_logit)  # returns normalized weights
        return wt, wa

    def fuse(self, text_results: List[TextSegmentOutput], audio_results: List[AudioSegmentOutput]) -> List[FusionSegmentOutput]:
        fused: Dict[Tuple[SpeakerT, float, float, str], FusionSegmentOutput] = {}

        # Index text
        for t in text_results:
            k = _key(t.get("speaker","?"), t.get("start_time",0.0), t.get("end_time",0.0), t.get("text",""), self.nd)
            fused[k] = {
                "speaker": k[0],
                "text": k[3],
                "start_time": k[1],
                "end_time": k[2],
                "emotions": dict(t.get("emotions", {}))
            }

        # Merge audio
        for a in audio_results:
            # find matching (speaker,times)
            mk = None
            for k in fused.keys():
                if k[0]==a.get("speaker","?") and k[1]==round(float(a.get("start_time",0.0)), self.nd) and k[2]==round(float(a.get("end_time",0.0)), self.nd):
                    mk = k; break
            if mk is None:
                # create new entry with empty text
                k = _key(a.get("speaker","?"), a.get("start_time",0.0), a.get("end_time",0.0), "", self.nd)
                fused[k] = {
                    "speaker": k[0],
                    "text": "",
                    "start_time": k[1],
                    "end_time": k[2],
                    "emotions": {}
                }
                mk = k

            # Compute adaptive weights
            tmeta = None
            ameta = a.get("meta") if isinstance(a.get("meta"), dict) else None
            # try to collect tmeta from text side if available
            # (not stored separately; optional: DialogueService may pass 'meta' inside text_results and we can fetch it by matching key)
            wt, wa = self._infer_weights(tmeta, ameta)

            # Merge label-wise
            tmap = { _norm(k): v for k,v in fused[mk]["emotions"].items() }
            amap = { _norm(k): v for k,v in a.get("emotions", {}).items() }
            labels = set(tmap) | set(amap)
            out = {}
            for lab in labels:
                out[lab] = tmap.get(lab,0.0) * wt + amap.get(lab,0.0) * wa

            # Renormalize
            if self.renorm:
                s = sum(out.values())
                if s > 0:
                    for lab in list(out.keys()):
                        out[lab] /= s

            fused[mk]["emotions"] = out

        out_list = list(fused.values())
        out_list.sort(key=lambda r: (r["start_time"], str(r["speaker"])))
        return out_list

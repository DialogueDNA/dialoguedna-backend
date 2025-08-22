from __future__ import annotations
from typing import Dict, List
import math

from app.interfaces.services.emotions.mixed import (
    EmotionMixedAnalyzer,
    EmotionAnalyzerMixerInput,
    EmotionAnalyzerMixerOutput,
)
from .config import MixedAdaptiveConfig


def _norm_label(label: str) -> str:
    """Normalize label keys to a canonical form to align dictionaries."""
    return (label or "").strip().lower().replace(" ", "_")


def _collect_keys(text: Dict[str, float], audio: Dict[str, float]) -> List[str]:
    """Union of normalized keys from both modalities (stable order)."""
    keys = []
    seen = set()
    for src in (text, audio):
        for k in (src or {}).keys():
            nk = _norm_label(k)
            if nk not in seen:
                seen.add(nk)
                keys.append(nk)
    return keys


def _vectorize(src: Dict[str, float], keys: List[str], eps: float) -> List[float]:
    """Map emotion dict -> vector aligned to `keys`, clamped to [0,∞) then normalized."""
    vec = [max(float(src.get(k, 0.0)), 0.0) for k in keys]
    s = sum(vec)
    if s <= 0.0:
        # fallback: uniform tiny distribution (prevents NaNs and keeps neutrality)
        u = 1.0 / max(1, len(keys))
        return [u for _ in keys]
    # Normalize + floor to avoid exact zeros in geometric fusion
    vec = [max(v / s, eps) for v in vec]
    # Re-normalize after floor
    s = sum(vec)
    return [v / s for v in vec]


def _conf_from_entropy(vec: List[float], eps: float) -> float:
    """Confidence = 1 - normalized entropy ∈ [0,1]."""
    k = max(1, len(vec))
    h = -sum(v * math.log(max(v, eps)) for v in vec)
    h_max = math.log(k)
    return 1.0 - (h / h_max if h_max > 0 else 0.0)


def _cosine(p: List[float], q: List[float], eps: float) -> float:
    """Cosine similarity ∈ [0,1] for probability-like vectors."""
    num = sum(pi * qi for pi, qi in zip(p, q))
    dp = math.sqrt(sum(pi * pi for pi in p)) + eps
    dq = math.sqrt(sum(qi * qi for qi in q)) + eps
    c = num / (dp * dq)
    # clamp numeric drift
    return max(0.0, min(1.0, c))


class AdaptiveEmotionMixedMixer(EmotionMixedAnalyzer):
    """
    Adaptive fusion between one text result and one audio result.
    Fits the protocol:
      def fuse(self, mix_results: EmotionAnalyzerMixerInput) -> EmotionAnalyzerMixerOutput
    """

    def __init__(self, cfg: MixedAdaptiveConfig):
        self._cfg = cfg

    def fuse(self, mix_results: EmotionAnalyzerMixerInput) -> EmotionAnalyzerMixerOutput:
        # ---- Extract emotion_analysis dicts (maybe empty) ----
        text_emotions: Dict[str, float] = (mix_results.text_results or {}).emotions_intensity_dict
        audio_emotions: Dict[str, float] = (mix_results.audio_results or {}).emotions_intensity_dict

        # ---- Align labels and build probability vectors ----
        keys = _collect_keys(text_emotions, audio_emotions)
        if not keys:   # degenerate; return empty safely
            return EmotionAnalyzerMixerOutput(emotions_intensity_dict={})

        p_text = _vectorize({ _norm_label(k): v for k, v in text_emotions.items() }, keys, self._cfg.eps)
        p_audio = _vectorize({ _norm_label(k): v for k, v in audio_emotions.items() }, keys, self._cfg.eps)

        # ---- Per-segment confidences & agreement ----
        conf_t = _conf_from_entropy(p_text, self._cfg.eps)   # ∈ [0,1]
        conf_a = _conf_from_entropy(p_audio, self._cfg.eps)  # ∈ [0,1]
        agree  = _cosine(p_text, p_audio, self._cfg.eps)     # ∈ [0,1]

        # ---- Adaptive weights (then normalize) ----
        w_tilde_text  = self._cfg.w_text_conf  * conf_t + self._cfg.w_agreement * agree
        w_tilde_audio = self._cfg.w_audio_conf * conf_a + self._cfg.w_agreement * agree

        s = w_tilde_text + w_tilde_audio
        if s <= self._cfg.eps:
            w_text = w_audio = 0.5  # fallback
        else:
            w_text  = max(w_tilde_text  / s, self._cfg.eps)
            w_audio = max(w_tilde_audio / s, self._cfg.eps)
            # re-normalize after flooring
            s2 = w_text + w_audio
            w_text, w_audio = w_text / s2, w_audio / s2

        # ---- Fuse distributions ----
        if self._cfg.combine == "geometric":
            fused = [ (pt ** w_text) * (pa ** w_audio) for pt, pa in zip(p_text, p_audio) ]
        else:  # "linear"
            fused = [ w_text * pt + w_audio * pa for pt, pa in zip(p_text, p_audio) ]

        # Optionally renormalize
        if self._cfg.renorm:
            s = sum(fused)
            if s > 0:
                fused = [v / s for v in fused]

        # ---- Map back to label dict (use normalized keys) ----
        emotions = { k: float(v) for k, v in zip(keys, fused) }
        return EmotionAnalyzerMixerOutput(emotions_intensity_dict=emotions)

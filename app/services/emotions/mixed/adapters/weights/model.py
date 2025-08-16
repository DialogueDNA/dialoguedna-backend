from __future__ import annotations
from typing import Dict

from app.interfaces.services.emotions.mixed import (
    EmotionMixedAnalyzer,
    EmotionAnalyzerMixerInput,
    EmotionAnalyzerMixerOutput,
)

from .config import MixedWeightsConfig


def _norm_label(label: str) -> str:
    """Normalize label keys to a canonical form (lowercase, underscores)."""
    return (label or "").strip().lower().replace(" ", "_")


def _weighted_merge(
    text: Dict[str, float],
    audio: Dict[str, float],
    wt: float,
    wa: float,
    renorm: bool = True,
) -> Dict[str, float]:
    """
    Merge two emotion-score dicts with weights; optionally re-normalize to sum=1.
    """
    out: Dict[str, float] = {}
    t = {_norm_label(k): float(v) for k, v in (text or {}).items()}
    a = {_norm_label(k): float(v) for k, v in (audio or {}).items()}
    keys = set(t) | set(a)
    for k in keys:
        out[k] = t.get(k, 0.0) * wt + a.get(k, 0.0) * wa

    if renorm:
        s = sum(out.values())
        if s > 0.0:
            for k in out.keys():
                out[k] = out[k] / s
    return out


class MixEmotionMixedByWeights(EmotionMixedAnalyzer):
    """
    Weighted fusion of a single text result and a single audio result.

    Input:
      - EmotionAnalyzerMixerInput with:
          text_results: EmotionAnalyzerOutput(emotion_analysis: Dict[str, float])
          audio_results: EmotionAnalyzerOutput(emotion_analysis: Dict[str, float])

    Output:
      - EmotionAnalyzerMixerOutput == EmotionAnalyzerOutput of fused scores.
    """
    def __init__(self, cfg: MixedWeightsConfig):
        if cfg.text_weight < 0 or cfg.audio_weight < 0 or (cfg.text_weight + cfg.audio_weight) == 0:
            raise ValueError("Invalid fusion weights (must be non-negative and not both zero).")
        s = cfg.text_weight + cfg.audio_weight
        self._wt = cfg.text_weight / s
        self._wa = cfg.audio_weight / s
        self._renorm = cfg.renorm

    def fuse(self, mix_results: EmotionAnalyzerMixerInput) -> EmotionAnalyzerMixerOutput:
        text_emotions = (mix_results.text_results or {}).emotions
        audio_emotions = (mix_results.audio_results or {}).emotions
        fused = _weighted_merge(text_emotions, audio_emotions, self._wt, self._wa, self._renorm)
        return EmotionAnalyzerMixerOutput(emotions=fused)

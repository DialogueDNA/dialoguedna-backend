# Path: app/services/emotions_new/mixer/labels.py
# Purpose: Canonical label orders + small helpers for conversions.
# Notes:
#   - Keep these arrays as the single source of truth for label order.
#   - Helpers are tiny and dependency-free.

from __future__ import annotations

from typing import Dict, List

EMOTIONS_6 = ["anger", "disgust", "fear", "joy", "sadness", "surprise"]
EMOTIONS_4 = ["angry", "happy", "sad", "neutral"]


def list_to_vec(labels_scores: List[Dict[str, float]], order: List[str]) -> List[float]:
    """
    Convert [{"label":l,"score":p},...] into a dense vector aligned to `order`.
    Missing labels default to 0.
    """
    by = {str(it["label"]).lower(): float(it["score"]) for it in labels_scores}
    return [float(by.get(lbl, 0.0)) for lbl in order]


def vec_to_list(vec: List[float], order: List[str]) -> List[Dict[str, float]]:
    """Convert a vector back to [{"label":..., "score":...}], sorted desc."""
    pairs = [{"label": lbl, "score": float(p)} for lbl, p in zip(order, vec)]
    pairs.sort(key=lambda x: x["score"], reverse=True)
    return pairs

def vec_to_list_pct(vec: List[float], order: List[str], decimals: int = 1) -> List[Dict[str, float]]:
    """Convert probs (sum=1) to [{"label", "score_pct"}], sorted desc."""
    pairs = [{"label": lbl, "score_pct": round(float(p) * 100.0, decimals)} for lbl, p in zip(order, vec)]
    pairs.sort(key=lambda x: x["score_pct"], reverse=True)
    # Small renorm to keep ~100 after rounding (optional; can omit)
    total = sum(x["score_pct"] for x in pairs)
    if total and abs(total - 100.0) > 0.5:
        scale = 100.0 / total
        for x in pairs:
            x["score_pct"] = round(x["score_pct"] * scale, decimals)
    return pairs

def to_api_top1(vec: List[float], order: List[str]) -> Dict[str, float]:
    """Return the top-1 as {"label": ..., "score": ...}."""
    if not vec:
        return {"label": order[0], "score": 0.0}
    idx = max(range(len(vec)), key=lambda i: vec[i])
    return {"label": order[idx], "score": float(vec[idx])}

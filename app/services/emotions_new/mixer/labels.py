# Path: app/services/emotions_new/mixer/labels.py
# Purpose: Canonical label orders + small helpers for conversions.

from __future__ import annotations
from typing import Dict, List

# Single source of truth for label order
EMOTIONS_7 = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]
EMOTIONS_4 = ["angry", "happy", "sad", "neutral"]


def list_to_vec(labels_scores: List[Dict[str, float]], order: List[str]) -> List[float]:
    """
    Convert [{"label": l, "score": p}, ...] into a dense vector aligned to `order`.
    - Accepts scores in probabilities [0..1]. If values look like percentages (>1), scales by /100.
    - Missing labels default to 0.
    """
    by: Dict[str, float] = {}
    for it in labels_scores or []:
        lbl = str(it.get("label", "")).lower()
        val = float(it.get("score", 0.0))
        if val > 1.0:  # tolerate percentages
            val /= 100.0
        by[lbl] = val
    return [float(by.get(lbl, 0.0)) for lbl in order]


def vec_to_list(vec: List[float], order: List[str]) -> List[Dict[str, float]]:
    """Convert a vector back to [{"label":..., "score":...}] (probabilities), sorted desc."""
    pairs = [{"label": lbl, "score": float(p)} for lbl, p in zip(order, vec)]
    pairs.sort(key=lambda x: x["score"], reverse=True)
    return pairs


def vec_to_list_pct(vec: List[float], order: List[str], decimals: int = 4) -> List[Dict[str, float]]:
    """
    LEGACY: Convert probabilities (sum≈1) to [{"label","score"}] where score ∈ [0..1], sorted desc.
    Drops 'neutral' and renormalizes to keep sum≈1 after rounding.
    """
    # 1) build as probabilities (no %)
    pairs = [{"label": lbl, "score": round(float(p), decimals)} for lbl, p in zip(order, vec)]

    # 2) drop neutral (legacy = 6 רגשות)
    pairs = [x for x in pairs if x["label"] != "neutral"]

    # 3) sort desc
    pairs.sort(key=lambda x: x["score"], reverse=True)

    # 4) renorm to 1.0 after rounding
    total = sum(x["score"] for x in pairs)
    if total and abs(total - 1.0) > 1e-6:
        scale = 1.0 / total
        for x in pairs:
            x["score"] = round(x["score"] * scale, decimals)

    return pairs



def to_api_top1(vec: List[float], order: List[str]) -> Dict[str, float]:
    """Return the top-1 as {"label": ..., "score": ...} with score in probability space [0..1]."""
    if not vec:
        return {"label": order[0], "score": 0.0}
    idx = max(range(len(vec)), key=lambda i: vec[i])
    return {"label": order[idx], "score": float(vec[idx])}

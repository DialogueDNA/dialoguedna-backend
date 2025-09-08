# app/services/emotions_new/mixer/labels.py
# Canonical label orders + small helpers for conversions.

from __future__ import annotations
from typing import Dict, List

from app.core.config import(EMOTIONS_7,EMOTIONS_4)

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


def vec_to_list_pct(vec: List[float], order: List[str], decimals: int = 1) -> List[Dict[str, float]]:
    """Convert probs (sum=1) to [{"label","score"}] in percent, sorted desc."""
    pairs = [{"label": lbl, "score": round(float(p) * 100.0, decimals)} for lbl, p in zip(order, vec)]
    pairs.sort(key=lambda x: x["score"], reverse=True)
    total = sum(x["score"] for x in pairs)
    if total and abs(total - 100.0) > 0.5:
        scale = 100.0 / total
        for x in pairs:
            x["score"] = round(x["score"] * scale, decimals)
    return pairs



def to_api_top1(vec: List[float], order: List[str]) -> Dict[str, float]:
    """Return the top-1 as {"label": ..., "score": ...} with score in probability space [0..1]."""
    if not vec:
        return {"label": order[0], "score": 0.0}
    idx = max(range(len(vec)), key=lambda i: vec[i])
    return {"label": order[idx], "score": float(vec[idx])}

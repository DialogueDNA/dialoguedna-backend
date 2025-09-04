# Path: app/services/emotions_new/mixer/normalize.py
# Purpose: Numeric helpers for weighting and normalization (no business logic).

from __future__ import annotations

from typing import List


def renorm(vec: List[float]) -> List[float]:
    """Clamp negatives to 0, then renormalize to sum=1 (uniform if all zeros)."""
    xs = [max(0.0, float(v)) for v in vec]
    s = sum(xs)
    if s <= 0.0:
        n = len(xs) if xs else 1
        return [1.0 / n] * n
    return [v / s for v in xs]


def weighted_sum(*terms: List[float], weights: List[float]) -> List[float]:
    """Compute Σ w_i * term_i elementwise. Assumes equal length vectors."""
    if not terms:
        return []
    n = len(terms[0])
    out = [0.0] * n
    for term, w in zip(terms, weights):
        for i in range(n):
            out[i] += float(w) * float(term[i])
    return out

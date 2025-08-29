from __future__ import annotations

from typing import Dict


def _norm(label: str) -> str:
    return (label or "").strip().lower().replace(" ", "_")


def fuse_emotions(text: Dict[str, float], audio: Dict[str, float], *, text_weight: float = 0.4,
                  audio_weight: float = 0.6, renorm: bool = True) -> Dict[str, float]:
    s = float(text_weight + audio_weight) or 1.0
    wt, wa = text_weight / s, audio_weight / s
    t = {_norm(k): float(v) for k, v in (text or {}).items()}
    a = {_norm(k): float(v) for k, v in (audio or {}).items()}
    keys = set(t) | set(a)
    out = {k: t.get(k, 0.0) * wt + a.get(k, 0.0) * wa for k in keys}
    if renorm:
        ss = sum(out.values()) or 1.0
        out = {k: v / ss for k, v in out.items()}
    return out



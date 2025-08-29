from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class OverlapWindow:
    start: float
    end: float
    speakers: Tuple[str, ...]


def detect_overlaps(segments: List[dict]) -> List[OverlapWindow]:
    events: List[Tuple[float, str, int]] = []
    for s in segments:
        st = s.get("start_time"); et = s.get("end_time"); spk = s.get("speaker")
        if st is None or et is None or spk is None:
            continue
        events.append((float(st), str(spk), +1))
        events.append((float(et), str(spk), -1))
    events.sort(key=lambda x: (x[0], -x[2]))

    active: Dict[str, int] = {}
    last_t: Optional[float] = None
    windows: List[OverlapWindow] = []
    for t, spk, delta in events:
        if last_t is not None and t > last_t:
            speakers_now = tuple(sorted([k for k, v in active.items() if v > 0]))
            if len(speakers_now) >= 2:
                windows.append(OverlapWindow(start=last_t, end=t, speakers=speakers_now))
        active[spk] = active.get(spk, 0) + delta
        if active[spk] <= 0:
            active.pop(spk, None)
        last_t = t

    merged: List[OverlapWindow] = []
    for w in windows:
        if merged and merged[-1].speakers == w.speakers and abs(merged[-1].end - w.start) < 1e-6:
            merged[-1] = OverlapWindow(start=merged[-1].start, end=w.end, speakers=w.speakers)
        else:
            merged.append(w)
    return merged


def subtract_interval(intervals: List[Tuple[float, float]], cut: Tuple[float, float]) -> List[Tuple[float, float]]:
    c0, c1 = cut
    out: List[Tuple[float, float]] = []
    for a, b in intervals:
        if c1 <= a or c0 >= b:
            out.append((a, b))
        else:
            if c0 > a:
                out.append((a, min(b, c0)))
            if c1 < b:
                out.append((max(a, c1), b))
    return [(x, y) for (x, y) in out if y - x > 1e-6]



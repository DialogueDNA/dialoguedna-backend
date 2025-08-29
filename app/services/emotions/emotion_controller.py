from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.services.emotions.text_analyzer import TextEmotionAnalyzer
from app.services.emotions.tone_analyzer import SuperbToneEmotionAnalyzer, AudioSegment
from app.services.emotions.mixer import fuse_emotions
from app.services.emotions.audio_segments import detect_overlaps, subtract_interval


class EmotionController:
    """
    Orchestrates text emotions, tone emotions, and mixed fusion per transcript row.
    Expects transcript as a list of dicts with keys: speaker, text, start_time, end_time.
    """

    def __init__(self, *, audio_weight: float = 0.6, text_weight: float = 0.4, device: str = "cpu") -> None:
        self._text_analyzer = TextEmotionAnalyzer()
        self._tone_analyzer = SuperbToneEmotionAnalyzer(device=device)
        self._w_audio = audio_weight
        self._w_text = text_weight

    def analyze(self, *, transcript: List[Dict[str, Any]], audio_path: str) -> List[Dict[str, Any]]:
        text_maps = self._text_analyzer.analyze_transcript(transcript)
        out: List[Dict[str, Any]] = []

        # Pre-compute overlap windows across transcript
        overlap_windows = detect_overlaps(transcript)

        for idx, row in enumerate(transcript):
            st = row.get("start_time"); et = row.get("end_time")
            spk = row.get("speaker")

            # Default: empty audio map
            tone_map: Dict[str, float] = {}

            if st is not None and et is not None:
                # Build sub-intervals = overlap sub-windows for this speaker + remaining non-overlap
                intervals: List[Tuple[float, float]] = []
                remaining: List[Tuple[float, float]] = [(float(st), float(et))]

                for w in overlap_windows:
                    if w.end <= st or w.start >= et:
                        continue
                    if spk is None or str(spk) not in w.speakers:
                        continue
                    a = max(float(st), float(w.start))
                    b = min(float(et), float(w.end))
                    if b > a:
                        intervals.append((a, b))
                        remaining = subtract_interval(remaining, (a, b))

                # Add remaining non-overlap parts
                for (a, b) in remaining:
                    if b > a:
                        intervals.append((a, b))

                # Analyze each interval and duration-weight average
                parts: List[Tuple[float, Dict[str, float]]] = []
                dur_total = 0.0
                for (a, b) in intervals:
                    seg = AudioSegment(audio=audio_path, start_time=a, end_time=b)
                    d = self._tone_analyzer.analyze(seg).emotions_intensity_dict
                    dur = max(0.0, b - a)
                    if d and dur > 0:
                        parts.append((dur, d))
                        dur_total += dur

                if parts:
                    # Normalize each part, then weight-average by duration
                    labels = set().union(*[list(p[1].keys()) for p in parts])
                    acc: Dict[str, float] = {k: 0.0 for k in labels}
                    total = dur_total or 1.0
                    for dur, dist in parts:
                        s = float(sum(max(0.0, v) for v in dist.values())) or 1.0
                        w = dur / total
                        for k in labels:
                            acc[k] += w * (max(0.0, dist.get(k, 0.0)) / s)
                    # renorm
                    sacc = float(sum(acc.values())) or 1.0
                    tone_map = {k: v / sacc for k, v in acc.items()}

            mixed_map = fuse_emotions(text_maps[idx] or {}, tone_map or {}, text_weight=self._w_text, audio_weight=self._w_audio, renorm=True)

            out.append({
                "speaker": spk,
                "start_time": st,
                "end_time": et,
                "text": text_maps[idx],
                "audio": tone_map,
                "fused": mixed_map,
            })

        return out

    # Backwards-compatible facade API
    def get_emotions(self, *, transcript: List[Dict[str, Any]], audio_path: str) -> List[Dict[str, Any]]:
        return self.analyze(transcript=transcript, audio_path=audio_path)



# audio_pipeline/overlap_detector.py

from typing import List, Dict, Tuple

class OverlapDetector:
    def __init__(self, segments: List[Dict]):
        self.segments = segments

    def find_overlaps(self) -> List[Dict]:
        """
        Finds overlapping segments between different speakers.
        Returns a list of:
        {
            "start": float,
            "end": float,
            "speakers": [speaker1, speaker2, ...]
        }
        """
        overlaps = []
        for i in range(len(self.segments)):
            seg_a = self.segments[i]
            for j in range(i + 1, len(self.segments)):
                seg_b = self.segments[j]

                if seg_a["speaker"] != seg_b["speaker"]:
                    if self._is_overlap(seg_a, seg_b):
                        start = max(seg_a["start"], seg_b["start"])
                        end = min(seg_a["end"], seg_b["end"])
                        speakers = sorted(list({seg_a["speaker"], seg_b["speaker"]}))
                        overlaps.append({
                            "start": start,
                            "end": end,
                            "speakers": speakers
                        })

        return overlaps

    def _is_overlap(self, seg1: Dict, seg2: Dict) -> bool:
        return seg1["end"] > seg2["start"] and seg2["end"] > seg1["start"]

# audio_pipeline/base.py

from typing import List, Dict

class DiarizationResult:
    def __init__(self, segments: List[Dict]):
        self.segments = segments

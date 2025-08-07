# audio_pipeline/emotion_fusion.py

from typing import Dict
import collections

class EmotionFusion:
    def __init__(self, audio_weight: float = 0.6, text_weight: float = 0.4):
        assert 0 <= audio_weight <= 1
        assert 0 <= text_weight <= 1
        assert abs((audio_weight + text_weight) - 1.0) < 1e-6
        self.audio_weight = audio_weight
        self.text_weight = text_weight

    def fuse(self, audio_scores: Dict[str, float], text_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Combines audio + text scores into a single score per emotion.
        Returns: Dict of {label: fused_score}
        """
        all_labels = set(audio_scores.keys()).union(text_scores.keys())
        fused = {}
        for label in all_labels:
            audio_score = audio_scores.get(label, 0.0)
            text_score = text_scores.get(label, 0.0)
            fused[label] = (
                self.audio_weight * audio_score +
                self.text_weight * text_score
            )
        return fused

    def get_top_emotion(self, fused_scores: Dict[str, float]) -> str:
        return max(fused_scores.items(), key=lambda x: x[1])[0]

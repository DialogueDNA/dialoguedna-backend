# Path: app/services/emotions_new/speaker_emotion_state/label_stability.py
# Purpose: Prevent rapid label flips (hysteresis) by blending with the previous label
#          unless the new leader is sufficiently ahead.
# API:
#   adjusted_probs6, flags = LabelStabilizer.stabilize(prev_label, prev_prob, current_probs6,
#                                                      margin_threshold=0.15, blend_prev=0.3)
# Notes:
#   - margin = (current_top_prob - prev_prob) if the top label changed; else 0 → keep as is.
#   - If margin < threshold → blend some mass back to the previous label.
#   - Returns flags for transparency ("low_margin", "kept_previous").

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

try:
    from ..mixer.labels import EMOTIONS_6
except Exception:
    EMOTIONS_6 = ["anger", "disgust", "fear", "joy", "sadness", "surprise"]


def _renorm(vec: List[float]) -> List[float]:
    s = sum(max(0.0, v) for v in vec)
    if s <= 0.0:
        return [1.0 / len(vec)] * len(vec)
    return [max(0.0, v) / s for v in vec]


class LabelStabilizer:
    """Hysteresis/anti-flip helper for 6-class probabilities."""

    @staticmethod
    def stabilize(
        prev_label: Optional[str],
        prev_prob: float,
        current_probs6: List[float],
        margin_threshold: float = 0.15,
        blend_prev: float = 0.3,
    ) -> Tuple[List[float], Dict[str, bool]]:
        """
        Parameters
        ----------
        prev_label : str | None
            Previous decided label (may be None at start).
        prev_prob : float
            Probability of the previous label (confidence).
        current_probs6 : list[float]
            New distribution (sum≈1).
        margin_threshold : float
            Minimal lead over prev to allow switching labels without resistance.
        blend_prev : float
            If switching with low margin, how much mass to blend back to prev_label.

        Returns
        -------
        adjusted_probs6 : list[float]
            Possibly adjusted distribution (sum=1).
        flags : dict
            {"low_margin": bool, "kept_previous": bool}
        """
        probs = list(current_probs6)
        probs = _renorm(probs)
        flags = {"low_margin": False, "kept_previous": False}

        if prev_label is None or prev_label not in EMOTIONS_6:
            return probs, flags

        # Identify current top
        top_idx = max(range(len(probs)), key=lambda i: probs[i])
        top_lbl = EMOTIONS_6[top_idx]
        top_prob = probs[top_idx]

        if top_lbl == prev_label:
            # No change → keep as is
            return probs, flags

        # Switching labels: check margin vs. previous confidence
        margin = top_prob - float(prev_prob)
        if margin >= margin_threshold:
            # Strong enough to switch
            return probs, flags

        # Low margin → blend some probability back to previous label
        flags["low_margin"] = True
        prev_idx = EMOTIONS_6.index(prev_label)
        # Move a fraction of top mass to the previous label
        delta = blend_prev * probs[top_idx]
        probs[top_idx] = max(0.0, probs[top_idx] - delta)
        probs[prev_idx] = max(0.0, probs[prev_idx] + delta)
        probs = _renorm(probs)

        # If after blending the previous label leads again, note it
        new_top_idx = max(range(len(probs)), key=lambda i: probs[i])
        if new_top_idx == prev_idx:
            flags["kept_previous"] = True

        return probs, flags

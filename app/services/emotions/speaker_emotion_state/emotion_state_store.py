# Path: app/services/emotions_new/speaker_emotion_state/emotion_state_store.py
# Purpose: Rolling per-speaker emotional state (6-class) with simple decay + history.
# API:
#   store = EmotionStateStore()
#   state_probs6, last_label, last_prob = store.get(speaker_id)
#   store.update(speaker_id, fused_probs6, label)
# Notes:
#   - Keeps state per speaker: probs6 (sum=1), last_label, last_prob, and last 3 labels (for optional smoothing).
#   - Decay γ shrinks the previous state on each update to avoid “sticky” emotions.
#   - Pure logic; no dependencies on mixer or analyzers.

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

# Try to use the canonical labels; fall back if mixer.labels isn’t available yet.
try:
    from ..mixer.labels import EMOTIONS_6
except Exception:
    EMOTIONS_6 = ["anger", "disgust", "fear", "joy", "sadness", "surprise"]


def _renorm(vec: List[float]) -> List[float]:
    s = sum(max(0.0, v) for v in vec)
    if s <= 0.0:
        return [1.0 / len(vec)] * len(vec)
    return [max(0.0, v) / s for v in vec]


@dataclass
class _SpeakerState:
    probs6: List[float] = field(default_factory=lambda: [1.0 / len(EMOTIONS_6)] * len(EMOTIONS_6))
    last_label: Optional[str] = None
    last_prob: float = 0.0
    label_history: Deque[str] = field(default_factory=lambda: deque(maxlen=3))


class EmotionStateStore:
    """
    Minimal rolling state per speaker.
    - get(speaker_id) -> (state_probs6, last_label, last_prob)
    - update(speaker_id, fused_probs6, label) -> None
    """

    def __init__(self, gamma_decay: float = 0.85, blend_current: float = 0.7) -> None:
        """
        Parameters
        ----------
        gamma_decay : float
            Decay factor (0..1) applied to the previous state.
        blend_current : float
            Weight for current fused probs vs. decayed previous state (1-blend_current).
        """
        self.gamma = float(gamma_decay)
        self.alpha = float(blend_current)
        self._by_speaker: Dict[str, _SpeakerState] = {}

    # ---------- Public API ----------

    def get(self, speaker_id: str) -> Tuple[List[float], Optional[str], float]:
        """Return (state_probs6, last_label, last_prob) for this speaker."""
        st = self._by_speaker.get(speaker_id)
        if st is None:
            return [1.0 / len(EMOTIONS_6)] * len(EMOTIONS_6), None, 0.0
        return list(st.probs6), st.last_label, float(st.last_prob)

    def update(self, speaker_id: str, fused_probs6: List[float], label: str) -> None:
        """
        Update rolling state with the current fused probabilities and chosen label.

        - New state = renorm( alpha * current + (1 - alpha) * gamma * prev )
        - Tracks last_label/last_prob and keeps a short label history (len=3).
        """
        fused = _renorm(list(fused_probs6))
        st = self._by_speaker.get(speaker_id)
        if st is None:
            st = _SpeakerState()
            self._by_speaker[speaker_id] = st

        prev = st.probs6
        decayed_prev = [self.gamma * p for p in prev]
        new_state = _renorm([self.alpha * c + (1.0 - self.alpha) * p for c, p in zip(fused, decayed_prev)])

        st.probs6 = new_state
        st.last_label = str(label) if label is not None else None
        st.last_prob = max(fused) if fused else 0.0
        if st.last_label:
            st.label_history.append(st.last_label)

    # ---------- Optional helpers ----------

    def majority_label(self, speaker_id: str) -> Optional[str]:
        """Return the majority of the last up-to-3 labels (ties: return last_label)."""
        st = self._by_speaker.get(speaker_id)
        if not st or not st.label_history:
            return None
        counts: Dict[str, int] = {}
        for lbl in st.label_history:
            counts[lbl] = counts.get(lbl, 0) + 1
        # Argmax by count, tie-breaker = last_label
        best = max(counts.items(), key=lambda kv: (kv[1], kv[0] == (st.last_label or "")))[0]
        return best

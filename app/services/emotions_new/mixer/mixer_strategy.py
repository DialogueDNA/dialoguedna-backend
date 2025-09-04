# Path: app/services/emotions_new/mixer/mixer_strategy.py
# Purpose: Combine text(6) + tone(4) into a final 6-class distribution, then output Top-1 (legacy).
# Inputs:
#   - text_json:  {"utterances":[{speaker,text,start_time,end_time,emotions:[{label,score}×6]}]}
#   - tone_json:  {"utterances":[{speaker,start_time,end_time,emotions4:[{label,score}×4],confidence:float,qc:{...}}]}
# Output (legacy-compatible):
#   List[dict] with: {speaker, text, start_time, end_time, emotions: {"label":top, "score":p}}
# Policy (concise):
#   - Base weights: w_text=0.6, w_audio=0.4
#   - Weak/neutral tone (neutral top OR conf<0.45 OR duration<0.7s OR backchannel=True) → w_audio=0.1, w_text=0.9
#   - Strong tone (conf≥0.6 and not neutral) → w_audio=0.5, w_text=0.5
#   - Soft 3→6 mapping inside mixer (angry→anger 0.8 + disgust 0.2; happy→joy 0.9 + surprise 0.1; sad→sadness 1.0; neutral→zeros)
#   - Final vector = renorm( w_text * text6 + w_audio * mapped_audio6 )
#   - Final public output = Top-1 only (label+score), same shape as the old system.

from __future__ import annotations
from typing import Any, Dict, List

from .labels import EMOTIONS_6, EMOTIONS_4, list_to_vec, to_api_top1, vec_to_list_pct
from .normalize import renorm, weighted_sum


class MixerStrategy:
    # ---- thresholds (can be moved to a central config later) ----
    DURATION_SHORT_SEC = 0.7
    CONF_WEAK = 0.45
    CONF_STRONG = 0.60

    BASE_W_TEXT = 0.60
    BASE_W_AUDIO = 0.40
    WEAK_AUDIO_W = 0.10
    STRONG_AUDIO_W = 0.50  # and 0.50 for text

    def mix(self, text_json: Dict[str, Any], tone_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return final results with ALL 6 emotions as percentages (sorted desc)."""
        t_utts = list(text_json.get("utterances", []))
        a_utts = list(tone_json.get("utterances", []))
        n = min(len(t_utts), len(a_utts))
        results: List[Dict[str, Any]] = []

        for i in range(n):
            t = t_utts[i];
            a = a_utts[i]

            text6 = list_to_vec(t.get("emotions", []), EMOTIONS_6)
            tone4 = list_to_vec(a.get("emotions4", []), EMOTIONS_4)
            conf = float(a.get("confidence", 0.0))
            qc = dict(a.get("qc", {}))
            is_back = bool(qc.get("is_backchannel", False))
            duration = float(
                qc.get("duration_sec", max(0.0, float(a.get("end_time", 0.0)) - float(a.get("start_time", 0.0)))))

            w_text, w_audio = self._weights_for(tone4, conf, duration, is_back)
            audio6 = self._soft_map_4_to_6(tone4)

            fused6 = renorm(weighted_sum(text6, audio6, weights=[w_text, w_audio]))
            emotions_pct = vec_to_list_pct(fused6, EMOTIONS_6, decimals=1)

            results.append({
                "speaker": t.get("speaker", a.get("speaker", "?")),
                "text": t.get("text", ""),
                "start_time": float(t.get("start_time", a.get("start_time", 0.0))),
                "end_time": float(t.get("end_time", a.get("end_time", 0.0))),
                "emotions": emotions_pct,  # ALL 6 as percentages
            })

        return results
    # ---------------- internal helpers ----------------

    def _weights_for(self, tone4: List[float], conf: float, duration: float, is_back: bool) -> tuple[float, float]:
        """Return (w_text, w_audio) based on tone strength and sentence conditions."""
        # Tone top label
        if tone4:
            top_idx = max(range(len(tone4)), key=lambda i: tone4[i])
            top_lbl = EMOTIONS_4[top_idx]
        else:
            top_lbl = "neutral"

        # Weak/neutral tone or very short/backchannel → text dominates
        if is_back or duration < self.DURATION_SHORT_SEC or top_lbl == "neutral" or conf < self.CONF_WEAK:
            return (0.90, self.WEAK_AUDIO_W)

        # Strong tone (not neutral) → balanced
        if conf >= self.CONF_STRONG and top_lbl != "neutral":
            return (1.0 - self.STRONG_AUDIO_W, self.STRONG_AUDIO_W)

        # Default
        return (self.BASE_W_TEXT, self.BASE_W_AUDIO)

    def _soft_map_4_to_6(self, tone4: List[float]) -> List[float]:
        """
        Soft mapping ONLY for informative classes (angry/happy/sad).
        neutral → zeros (no evidence).
        """
        if not tone4 or len(tone4) != 4:
            return [0.0] * len(EMOTIONS_6)

        angry, happy, sad, neutral = tone4

        # angry → anger 0.8 + disgust 0.2
        anger = 0.8 * angry
        disgust = 0.2 * angry

        # happy → joy 0.9 + surprise 0.1
        joy = 0.9 * happy
        surprise = 0.1 * happy

        # sad → sadness 1.0
        sadness = 1.0 * sad

        # fear gets a tiny share from none in tone (keep at 0 here; text should drive fear)
        fear = 0.0

        return [anger, disgust, fear, joy, sadness, surprise]


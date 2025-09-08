# app/services/emotions_new/mixer/mixer_strategy.py
# Combine text_emotions(7) + tone_emotions(4→7) into a final 7-class distribution.

from __future__ import annotations
from typing import Any, Dict, List
from .labels import EMOTIONS_7, EMOTIONS_4, list_to_vec, vec_to_list_pct
from .normalize import renorm, weighted_sum

class MixerStrategy:
    # ---- thresholds (can be moved to a central config later) ----
    DURATION_SHORT_SEC = 0.7
    AUDIO_CONFIDENT_WEAK = 0.45
    AUDIO_CONFIDENT_STRONG = 0.60
    WEIGHT_BASE_TEXT = 0.60
    WEIGHT_BASE_AUDIO = 0.40
    WEIGHT_IF_AUDIO_CONFIDENT_WEAK = 0.10
    WEIGHT_IF_AUDIO_CONFIDENT_STRONG = 0.50  # and 0.50 for text

    def mix(self, text_json: Dict[str, Any], tone_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return final results with ALL 7 emotions as percentages (sorted desc)."""
        text_utts = list(text_json.get("utterances", []))
        audio_utts = list(tone_json.get("utterances", []))
        aligned_utterance_pairs_count  = min(len(text_utts), len(audio_utts))
        results: List[Dict[str, Any]] = []

        for i in range(aligned_utterance_pairs_count ):

            text_utt  = text_utts[i];
            audio_utt  = audio_utts[i]

            text7  = list_to_vec(text_utt .get("emotions", []), EMOTIONS_7)
            tone4 = list_to_vec(audio_utt .get("emotions4", []), EMOTIONS_4)

            confidence  = float(audio_utt .get("confidence", 0.0))
            qc = dict(audio_utt .get("qc", {}))
            is_back = bool(qc.get("is_backchannel", False))
            duration = float(
                qc.get("duration_sec", max(0.0, float(audio_utt .get("end_time", 0.0)) - float(audio_utt .get("start_time", 0.0)))))

            text_weight, audio_weight  = self._weights_for(tone4, confidence , duration, is_back)

            audio7  = self._soft_map_4_to_7(tone4)

            fused7  = renorm(weighted_sum(text7 , audio7 , weights=[text_weight, audio_weight ]))

            emotions_pct = vec_to_list_pct(fused7 , EMOTIONS_7, decimals=1)

            results.append({
                "speaker": text_utt .get("speaker", audio_utt .get("speaker", "?")),
                "text": text_utt .get("text", ""),
                "start_time": float(text_utt .get("start_time", audio_utt .get("start_time", 0.0))),
                "end_time": float(text_utt .get("end_time", audio_utt .get("end_time", 0.0))),
                "emotions": emotions_pct,  # ALL 7 as percentages
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
        if is_back or duration < self.DURATION_SHORT_SEC or top_lbl == "neutral" or conf < self.AUDIO_CONFIDENT_WEAK:
            return (0.90, self.WEIGHT_IF_AUDIO_CONFIDENT_WEAK)

        # Strong tone (not neutral) → balanced
        if conf >= self.AUDIO_CONFIDENT_STRONG and top_lbl != "neutral":
            return (1.0 - self.WEIGHT_IF_AUDIO_CONFIDENT_STRONG, self.WEIGHT_IF_AUDIO_CONFIDENT_STRONG)

        # Default
        return (self.WEIGHT_BASE_TEXT, self.WEIGHT_BASE_AUDIO)

    def _soft_map_4_to_7(self, tone4: List[float]) -> List[float]:
        """
        Soft mapping ONLY for informative classes (angry/happy/sad).
        neutral → zeros (no evidence).
        """
        if not tone4 or len(tone4) != 4:
            return [0.0] * len(EMOTIONS_7)

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

        neutral = 1.0 * neutral

        return [anger, disgust, fear, joy, sadness, surprise, neutral]


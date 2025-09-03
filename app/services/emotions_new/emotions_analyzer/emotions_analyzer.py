# Path: app/services/emotions_new/emotions_analyzer/emotions_analyzer.py
# Purpose: Orchestrator ("commander") for per-utterance emotion analysis.
# Inputs: utterance {speaker_id, text, start_time, end_time, audio_ref}; top_k.
# Flow: call text analyzer + tone analyzer + state store + mixer strategy.
# Outputs: probs6 (sum=1), label, confidence, flags, updated speaker state.
# Notes: Designed to replace a single pipeline line without changing I/O.
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from ..text_base_analysis.text_base_analyzer import TextBaseAnalyzer
from ..tone_base_analysis.tone_base_analyzer import ToneBaseAnalyzer
from ..mixer.mixer_strategy import MixerStrategy


def __init__(
        self,
        text_analyzer: TextBaseAnalyzer | None = None,
        tone_analyzer: ToneBaseAnalyzer | None = None,
        mixer: MixerStrategy | None = None,
) -> None:
    # Lazy/default components (can be injected for testing)
    self.text_analyzer = text_analyzer or TextBaseAnalyzer()
    self.tone_analyzer = tone_analyzer or ToneBaseAnalyzer()
    self.mixer = mixer or MixerStrategy()

    def analyze_emotions(
        self,
        transcript_json: Dict[str, Any],
        audio_blob_path: Union[str, Path],
    ) -> List[Dict[str, Any]]:

        # 1) Text path → probs6 per utterance
        text_emotions_json: Dict[str, Any] = self.text_analyzer.analyze(transcript_json)

         # 2) Tone path → probs4 per segment → mapped probs6 (+ qc)
        tone_emotions_json: Dict[str, Any] = self.tone_analyzer.analyze(audio_blob_path, transcript_json)

        # 3) Mix → final emotions (6)
        final_emotions_json: Dict[str, Any] = self.mixer.mix(text_emotions_json,tone_emotions_json)

        return final_emotions_json



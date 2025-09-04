# Path: app/services/emotions_new/emotions_analyzer/emotions_analyzer.py
# Purpose: Orchestrator ("commander") for per-utterance emotion analysis.
# Inputs: utterance {speaker_id, text, start_time, end_time, audio_ref}; top_k.
# Flow: call text analyzer + tone analyzer + state store + mixer strategy.
# Outputs: probs6 (sum=1), label, confidence, flags, updated speaker state.
# Notes: Designed to replace a single pipeline line without changing I/O.
import json
from pathlib import Path
from typing import Any, Dict, List, Union

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
        transcript_json: Dict[str, Any],          # expect dict with "utterances"
        audio_blob_path: Union[str, Path],
    ) -> List[Dict[str, Any]]:
        # 1) Text → expects a LIST of sentences
        utterances: List[Dict[str, Any]] = list(transcript_json.get("utterances", []))
        text_out: List[Dict[str, Any]] = self.text_analyzer.analyze(utterances)
        text_emotions_json: Dict[str, Any] = {"utterances": text_out}

        # 2) Tone → expects the DICT with "utterances"
        tone_emotions_json: Dict[str, Any] = self.tone_analyzer.analyze(audio_blob_path, transcript_json)

        # 3) Mix → final (all 6 emotions as percentages)
        final_emotions_results: List[Dict[str, Any]] = self.mixer.mix(text_emotions_json, tone_emotions_json)
        return final_emotions_results

    def save_results(
            text_json: Dict[str, Any],
            tone_json: Dict[str, Any],
            final_json: List[Dict[str, Any]],
            base_dir: Union[str, Path] | None = None,
    ) -> Path:
        """
        Save debug artifacts under:
          app/services/emotions_new/results/sessions/<session_name>/
        <session_name> is an incrementing integer: 1,2,3,...

        Files saved in the session folder:
          - text_json.json
          - tone_json.json
          - final_json.json

        Returns
        -------
        Path : the created session directory.
        """
        # Resolve default base dir relative to this file:
        # .../emotions_new/results/sessions
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1] / "results" / "sessions"
        else:
            base_dir = Path(base_dir)

        base_dir.mkdir(parents=True, exist_ok=True)

        # Determine next session name (numeric folders only)
        existing_nums = []
        for p in base_dir.iterdir():
            if p.is_dir() and p.name.isdigit():
                try:
                    existing_nums.append(int(p.name))
                except ValueError:
                    pass
        next_id = (max(existing_nums) + 1) if existing_nums else 1
        session_dir = base_dir / str(next_id)
        session_dir.mkdir(parents=False, exist_ok=False)

        # Helper to write JSON nicely (UTF-8, pretty)
        def _write(fp: Path, obj: Any) -> None:
            with fp.open("w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)

        _write(session_dir / "text_json.json", text_json)
        _write(session_dir / "tone_json.json", tone_json)
        _write(session_dir / "final_json.json", final_json)

        return session_dir


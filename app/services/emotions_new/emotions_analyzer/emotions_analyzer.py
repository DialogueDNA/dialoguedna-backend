# Path: app/services/emotions_new/emotions_analyzer/emotions_analyzer.py
# Purpose: Orchestrator ("commander") for per-utterance emotion analysis.
# Inputs: utterance {speaker_id, text, start_time, end_time, audio_ref}; top_k.
# Flow: call text analyzer + tone analyzer + state store + mixer strategy.
# Outputs: probs6 (sum=1), label, confidence, flags, updated speaker state.
# Notes: Designed to replace a single pipeline line without changing I/O.
# Path: app/services/emotions_new/emotions_analyzer/emotions_analyzer.py
import json
from pathlib import Path
from typing import Any, Dict, List, Union, IO, cast

from ..text_base_analysis.text_base_analyzer import TextBaseAnalyzer
from ..tone_base_analysis.tone_base_analyzer import ToneBaseAnalyzer
from ..mixer.mixer_strategy import MixerStrategy


class EmotionsAnalyzer:
    def __init__(
        self,
        text_analyzer: TextBaseAnalyzer | None = None,
        tone_analyzer: ToneBaseAnalyzer | None = None,
        mixer: MixerStrategy | None = None,
    ) -> None:
        self.text_analyzer = text_analyzer or TextBaseAnalyzer()
        self.tone_analyzer = tone_analyzer or ToneBaseAnalyzer()
        self.mixer = mixer or MixerStrategy()

    def analyze_emotions(
            self,
            transcript_input: Union[Dict[str, Any], List[Dict[str, Any]]],
            audio_blob_path: Union[str, Path],
    ) -> List[Dict[str, Any]]:
        # --- Normalize input ---
        if isinstance(transcript_input, dict):
            sentences: List[Dict[str, Any]] = list(transcript_input.get("utterances", []))
            tone_in: Dict[str, Any] = transcript_input  # keep metadata if exists
        else:
            sentences = list(transcript_input)
            tone_in = {"utterances": sentences}

        # --- 1) Text (6-class) ---
        text_out: List[Dict[str, Any]] = self.text_analyzer.analyze(sentences)
        text_json: Dict[str, Any] = {"utterances": text_out}

        # --- 2) Tone (4-class + confidence + qc) ---
        tone_json: Dict[str, Any] = self.tone_analyzer.analyze(audio_blob_path, tone_in)

        # --- 3) Mix → ALL 6 as % (sorted) ---
        final_pct_results: List[Dict[str, Any]] = self.mixer.mix(text_json, tone_json)

        # --- 4) Save debug artifacts (text/tone/final as %) ---
        try:
            self.save_results(text_json, tone_json, final_pct_results)
        except Exception as e:
            print(f"⚠️ save_results failed: {e}")

        # --- 5) Adapt to legacy app format: Top-1 only (label + score 0..1) ---
        legacy_results: List[Dict[str, Any]] = []
        for item in final_pct_results:
            emotions_pct = item.get("emotions", []) or []
            if emotions_pct:
                top = emotions_pct[0]  # already sorted desc
                legacy_emotions = {
                    "label": str(top.get("label", "")),
                    "score": float(top.get("score_pct", 0.0)) / 100.0,  # back to 0..1
                }
            else:
                legacy_emotions = {"label": "joy", "score": 0.0}  # safe fallback

            legacy_results.append({
                "speaker": item.get("speaker", "?"),
                "text": item.get("text", ""),
                "start_time": float(item.get("start_time", 0.0)),
                "end_time": float(item.get("end_time", 0.0)),
                "emotions": legacy_emotions,
            })

        return legacy_results

    def save_results(
        self,
        text_json: Dict[str, Any],
        tone_json: Dict[str, Any],
        final_json: List[Dict[str, Any]],
        base_dir: Union[str, Path] | None = None,
    ) -> Path:
        """
        Save debug artifacts under:
          app/services/emotions_new/results/sessions/<N>/
        Files:
          - text_json.json
          - tone_json.json
          - final_json.json
        """
        # sessions dir
        base = Path(base_dir) if base_dir else Path(__file__).resolve().parents[1] / "results" / "sessions"
        # Some type checkers complain about kwargs on mkdir; this is safe at runtime:
        try:
            base.mkdir(parents=True, exist_ok=True)
        except TypeError:  # older stubs
            try:
                base.mkdir(parents=True)
            except FileExistsError:
                pass

        # next session id
        existing_nums = [int(p.name) for p in base.iterdir() if p.is_dir() and p.name.isdigit()]
        next_id = (max(existing_nums) + 1) if existing_nums else 1
        session_dir = base / str(next_id)
        session_dir.mkdir(exist_ok=False)

        def _write(path: Path, obj: Any) -> None:
            # Help static type checkers: json.dump expects SupportsWrite[str]
            with path.open("w", encoding="utf-8") as f:
                jf = cast(IO[str], f)
                json.dump(obj, jf, ensure_ascii=False, indent=2)

        _write(session_dir / "text_json.json", text_json)
        _write(session_dir / "tone_json.json", tone_json)
        _write(session_dir / "final_json.json", final_json)

        return session_dir


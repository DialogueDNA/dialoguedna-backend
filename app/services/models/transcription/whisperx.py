# app/services/transcription/whisperx_pipeline.py
# -*- coding: utf-8 -*-
"""
WhisperXPipeline: End-to-end OOP wrapper for WhisperX transcription + alignment + diarization.
- Automatically selects GPU if available, otherwise uses CPU.
- Keeps models in memory for multiple calls; add `unload_models()` to free VRAM/RAM.
- Minimal, production-friendly structure with clear English docs/comments (per project convention).
"""

from typing import Optional, Dict, Any, Tuple
import gc

import torch
import whisperx

import app.settings.config as model_config
from app.settings.environment import HUGGINGFACE_WHISPERX_TOKEN


class WhisperXPipeline:
    """
    High-level pipeline for:
      1) ASR with WhisperX (batched)
      2) Phoneme-level alignment
      3) Speaker diarization and word-level speaker attribution

    Parameters
    ----------
    model_size : str
        WhisperX model size (e.g., "large-v2").
    batch_size : int
        Batch size used during transcription.
    compute_type : str
        WhisperX compute type (e.g., "float16", "int8", "int8_float16").
    download_root : Optional[str]
        Optional local dir to cache/download WhisperX models.
    device : Optional[str]
        Force device ("cuda" / "cpu"). If None, auto-detects GPU → "cuda" else "cpu".
    hf_token : Optional[str]
        HuggingFace token for diarization pipeline (needed for some models).
    """

    def __init__(
        self,
        model_size: str = "large-v2",
        batch_size: int = getattr(model_config, "WHISPERX_BATCH_SIZE", 8),
        compute_type: str = getattr(model_config, "WHISPERX_COMPUTE_TYPE", "float16"),
        download_root: Optional[str] = None,
        device: Optional[str] = None,
        hf_token: Optional[str] = HUGGINGFACE_WHISPERX_TOKEN,
    ) -> None:
        # Auto-select device: prefer GPU if available
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.model_size = model_size
        self.batch_size = batch_size
        self.compute_type = compute_type
        self.download_root = download_root
        self.hf_token = hf_token

        # Lazy-loaded models: init to None and load on first use
        self._asr_model = None
        self._align_model = None
        self._align_metadata = None
        self._diarize_pipeline = None

    # ---- Model loading helpers ------------------------------------------------

    def _ensure_asr_model(self) -> None:
        """Load WhisperX ASR model if not already loaded."""
        if self._asr_model is None:
            self._asr_model = whisperx.load_model(
                self.model_size,
                self.device,
                compute_type=self.compute_type,
                download_root=self.download_root,
            )

    def _ensure_align_model(self, language_code: str) -> None:
        """Load alignment model/metadata for the detected language."""
        if self._align_model is None or self._align_metadata is None:
            self._align_model, self._align_metadata = whisperx.load_align_model(
                language_code=language_code,
                device=self.device,
            )

    def _ensure_diarize_pipeline(self) -> None:
        """Load diarization pipeline if not already loaded."""
        if self._diarize_pipeline is None:
            self._diarize_pipeline = whisperx.diarize.DiarizationPipeline(
                use_auth_token=self.hf_token,
                device=self.device,
            )

    # ---- Public API -----------------------------------------------------------

    def transcribe(
        self,
        audio_file: str,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        return_char_alignments: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the full pipeline on an audio file.

        Returns
        -------
        Dict[str, Any]
            {
              "language": <str>,
              "segments": <List[Dict]>  # final segments with speaker IDs,
              "diarize_segments": <Any> # raw diarization segments,
            }
        """
        # Load audio
        audio = whisperx.load_audio(audio_file)

        # 1) Transcribe
        self._ensure_asr_model()
        asr_result = self._asr_model.transcribe(
            audio, batch_size=self.batch_size
        )
        language = asr_result.get("language")

        # 2) Align
        self._ensure_align_model(language_code=language)
        aligned = whisperx.align(
            asr_result["segments"],
            self._align_model,
            self._align_metadata,
            audio,
            self.device,
            return_char_alignments=return_char_alignments,
        )

        # 3) Diarize + assign speakers
        self._ensure_diarize_pipeline()
        if min_speakers is not None or max_speakers is not None:
            diarize_segments = self._diarize_pipeline(
                audio,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )
        else:
            diarize_segments = self._diarize_pipeline(audio)

        with_speakers = whisperx.assign_word_speakers(diarize_segments, aligned)

        return {
            "language": language,
            "segments": with_speakers["segments"],
            "diarize_segments": diarize_segments,
        }

    def unload_models(self) -> None:
        """
        Free model memory (useful when running on limited GPU/CPU RAM).
        Call again later to lazy-reload as needed.
        """
        # Delete refs
        self._asr_model = None
        self._align_model = None
        self._align_metadata = None
        self._diarize_pipeline = None

        # Force garbage collection and clear CUDA cache
        gc.collect()
        if torch.cuda.is_available():
            import torch as _torch
            _torch.cuda.empty_cache()

    # Optional: context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.unload_models()


# ---- Example usage ------------------------------------------------------------
# from app.services.transcription.whisperx_pipeline import WhisperXPipeline
#
# pipeline = WhisperXPipeline(
#     model_size="large-v2",
#     batch_size=model_config.WHISPERX_BATCH_SIZE,
#     compute_type=model_config.WHISPERX_COMPUTE_TYPE,
#     download_root=None,  # e.g., "/models/whisperx"
# )
#
# output = pipeline.transcribe(
#     audio_file="/path/to/audio.wav",
#     min_speakers=None,  # or e.g., 2
#     max_speakers=None,  # or e.g., 3
#     return_char_alignments=False,
# )
#
# print(output["language"])
# print(output["diarize_segments"])
# print(output["segments"])  # final segments with speaker IDs

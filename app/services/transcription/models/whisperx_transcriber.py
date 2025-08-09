# app/services/transcription/models/whisperx_transcriber.py
from __future__ import annotations
from typing import Any
import gc
import logging
import torch
import whisperx

import app.settings.config as model_config
from app.settings.environment import HUGGINGFACE_WHISPERX_TOKEN

log = logging.getLogger("app.transcription.whisperx")

class WhisperXTranscriber:
    def __init__(
        self,
        *,
        model_size: str = "large-v2",
        batch_size: int = getattr(model_config, "WHISPERX_BATCH_SIZE", 8),
        compute_type: str = getattr(model_config, "WHISPERX_COMPUTE_TYPE", "float16"),
        download_root: str | None = None,
        device: str | None = None,
        hf_token: str | None = HUGGINGFACE_WHISPERX_TOKEN,
        return_char_alignments: bool = False,
        diar_min_speakers: int | None = None,
        diar_max_speakers: int | None = None,
    ) -> None:
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_size = model_size
        self.batch_size = batch_size
        self.compute_type = compute_type
        self.download_root = download_root
        self.hf_token = hf_token
        self.return_char_alignments = return_char_alignments
        self.diar_min = diar_min_speakers
        self.diar_max = diar_max_speakers

        self._asr = None
        self._align = None
        self._align_md = None
        self._diar = None

    def _ensure_asr(self) -> None:
        if self._asr is None:
            log.info("Loading WhisperX ASR model (%s)...", self.model_size)
            self._asr = whisperx.load_model(
                self.model_size,
                self.device,
                compute_type=self.compute_type,
                download_root=self.download_root,
            )

    def _ensure_align(self, language_code: str) -> None:
        if self._align is None or self._align_md is None:
            log.info("Loading WhisperX alignment model for language=%s", language_code)
            self._align, self._align_md = whisperx.load_align_model(
                language_code=language_code, device=self.device
            )

    def _ensure_diar(self) -> None:
        if self._diar is None:
            log.info("Loading WhisperX diarization pipeline...")
            self._diar = whisperx.diarize.DiarizationPipeline(
                use_auth_token=self.hf_token, device=self.device
            )

    def transcribe(self, audio_path: str) -> list[dict[str, Any]]:
        log.info("Starting WhisperX transcription for: %s", audio_path)
        audio = whisperx.load_audio(audio_path)

        self._ensure_asr()
        asr = self._asr.transcribe(audio, batch_size=self.batch_size)
        lang = asr.get("language")
        log.info("Detected language: %s", lang)

        self._ensure_align(language_code=lang)
        aligned = whisperx.align(
            asr["segments"],
            self._align,
            self._align_md,
            audio,
            self.device,
            return_char_alignments=self.return_char_alignments,
        )

        self._ensure_diar()
        if self.diar_min is not None or self.diar_max is not None:
            diar = self._diar(audio, min_speakers=self.diar_min, max_speakers=self.diar_max)
        else:
            diar = self._diar(audio)

        with_speakers = whisperx.assign_word_speakers(diar, aligned)
        segments = with_speakers.get("segments", [])

        log.info("Transcription complete with %d segments.", len(segments))

        lines: list[dict[str, Any]] = []
        for s in segments:
            speaker = s.get("speaker") or s.get("speaker_id") or "?"
            text = s.get("text", "")
            start = float(s.get("start", 0.0))
            end = float(s.get("end", start))
            lines.append({
                "speaker": speaker,
                "text": text,
                "start_time": round(start, 2),
                "end_time": round(end, 2),
            })
        return lines

    def unload(self) -> None:
        log.info("Unloading WhisperX models and clearing memory.")
        self._asr = None
        self._align = None
        self._align_md = None
        self._diar = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

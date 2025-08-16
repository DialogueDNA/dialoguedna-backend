from __future__ import annotations
from typing import List, Optional

import numpy as np
import torch
import whisperx

from app.core.config.providers.whisperx import WhisperXConfig
from app.interfaces.services.transcription import (
    Transcriber,
    TranscriptionSegmentInput,
    TranscriptionSegmentOutput,
)
from app.interfaces.services.text import TextSegment
from app.interfaces.services.audio import AudioSegment


class WhisperXTranscriber(Transcriber):
    """
    WhisperX Transcriber that returns a list of TextSegment(s):
      - diarization=True (+ HF token available) -> segments split by speaker (time-contiguous chunks)
      - otherwise -> a single merged TextSegment
    """

    def __init__(self, cfg: WhisperXConfig):
        self._cfg = cfg
        self.device = cfg.device or "cpu"
        self.model = whisperx.load_model(cfg.model_size, self.device, compute_type=cfg.compute_type)
        self.hf_token = cfg.hf_token

        self._align_model = None
        self._align_meta = None
        self._diar = None
        self._batch_size: int = getattr(cfg, "batch_size", 16)

    # ---------------- Public API ----------------
    @torch.inference_mode()
    def transcribe(self, segment: TranscriptionSegmentInput) -> List[TranscriptionSegmentOutput]:
        audio: AudioSegment = segment.audio

        # 1) Prepare audio as 16k, mono, float32 numpy array
        audio_16k = self._prepare_audio_16k(audio)

        # 2) ASR
        asr_out = self.model.transcribe(audio_16k, batch_size=self._batch_size)
        language: Optional[str] = asr_out.get("language") or None
        segments: List[dict] = asr_out.get("segments") or []

        # 3) Alignment (improves timings)
        aligned = segments
        if language:
            self._ensure_alignment(language)
            if self._align_model is not None:
                try:
                    align_res = whisperx.align(
                        segments,
                        self._align_model,
                        self._align_meta,
                        audio_16k,
                        self.device,
                        return_char_alignments=False,
                    )
                    aligned = align_res.get("segments") or segments
                except Exception:
                    aligned = segments

        # 4) Diarization (optional)
        do_diary = bool(segment.diarization) and bool(self.hf_token)
        if do_diary:
            self._ensure_diar()
            try:
                diar_segments = self._diar(audio_16k)
                aligned = whisperx.assign_word_speakers(diar_segments, {"segments": aligned}).get("segments", aligned)
            except Exception:
                # diarization failed — fall back to merged single segment
                pass

        # 5) Build output(s)
        if do_diary:
            # explode to speaker-contiguous chunks if we have word-level speakers
            chunks = self._explode_by_speaker_chunks(aligned, language=language)
            if chunks:
                return chunks

        # fallback / non-diarization: single merged segment
        full_text = " ".join((s.get("text") or "").strip() for s in aligned if s.get("text"))
        start_time = audio.start_time if audio.start_time is not None else (aligned[0].get("start", 0.0) if aligned else None)
        end_time = audio.end_time if audio.end_time is not None else (
            (aligned[-1].get("end") or aligned[-1].get("start")) if aligned else None
        )
        return [TextSegment(writer=audio.speaker, text=full_text or "", start_time=start_time, end_time=end_time, language=language)]

    # ---------------- Internals ----------------
    def _prepare_audio_16k(self, audio: AudioSegment) -> np.ndarray:
        """Return mono 16 kHz float32 numpy array in [-1,1]."""
        obj = audio.audio
        if isinstance(obj, torch.Tensor):
            wf = obj.detach().cpu()
            if wf.dim() == 1:
                wf = wf.unsqueeze(0)  # [1, T]
            if wf.size(0) > 1:
                wf = wf.mean(dim=0, keepdim=True)
            sr = int(audio.sample_rate or 16_000)
            if sr != 16_000:
                wf = self._resample_torch(wf, sr, 16_000)
            wf = wf.squeeze(0).to(torch.float32).clamp_(-1.0, 1.0)
            return wf.numpy()
        # Path-like: let whisperx decode & resample
        return whisperx.load_audio(str(obj))

    def _ensure_alignment(self, lang_code: str) -> None:
        if self._align_model is not None and self._align_meta is not None:
            return
        try:
            self._align_model, self._align_meta = whisperx.load_align_model(
                language_code=lang_code, device=self.device
            )
        except Exception:
            self._align_model, self._align_meta = None, None

    def _ensure_diar(self) -> None:
        if self._diar is not None:
            return
        self._diar = whisperx.diarize.DiarizationPipeline(use_auth_token=self.hf_token, device=self.device)

    @staticmethod
    def _resample_torch(wf: torch.Tensor, src_sr: int, dst_sr: int) -> torch.Tensor:
        assert wf.dim() == 2 and wf.size(0) == 1, "expected mono [1, T]"
        t_src = wf.size(1)
        t_dst = max(int(round(t_src * (dst_sr / float(src_sr)))), 1)
        x_src = torch.linspace(0.0, 1.0, steps=t_src, dtype=wf.dtype)
        x_dst = torch.linspace(0.0, 1.0, steps=t_dst, dtype=wf.dtype)
        out = torch.interp(x_dst, x_src, wf[0])
        return out.unsqueeze(0)

    # ---- Build speaker-contiguous TextSegments from aligned words ----
    @staticmethod
    def _explode_by_speaker_chunks(aligned_segments: List[dict], language: Optional[str]) -> List[TextSegment]:
        """
        Converts aligned segments with word-level speakers into contiguous speaker chunks.
        Each chunk becomes a TextSegment(writer=<speaker>, text=..., start_time, end_time, language).
        """
        out: List[TextSegment] = []
        for seg in aligned_segments:
            words = seg.get("words") or []
            if not words:
                # no word-level info; fall back to raw segment text if speaker exists
                spk = seg.get("speaker", None)
                if spk and seg.get("text"):
                    out.append(TextSegment(
                        writer=str(spk),
                        text=str(seg["text"]).strip(),
                        start_time=float(seg.get("start") or 0.0),
                        end_time=float(seg.get("end") or seg.get("start") or 0.0),
                        language=language,
                    ))
                continue

            # Iterate words, split when speaker changes
            cur_spk = None
            cur_start = None
            cur_text_tokens: List[str] = []
            prev_end = None

            for w in words:
                spk = w.get("speaker")
                word = (w.get("word") or "").strip()
                w_start = float(w.get("start") or seg.get("start") or 0.0)
                w_end = float(w.get("end") or w_start)

                if cur_spk is None:
                    # start new chunk
                    cur_spk = spk
                    cur_start = w_start
                    cur_text_tokens = [word]
                    prev_end = w_end
                elif spk != cur_spk and cur_text_tokens:
                    # flush chunk on speaker change
                    out.append(TextSegment(
                        writer=str(cur_spk) if cur_spk is not None else None,
                        text=" ".join(cur_text_tokens).strip(),
                        start_time=cur_start,
                        end_time=prev_end,
                        language=language,
                    ))
                    # start new
                    cur_spk = spk
                    cur_start = w_start
                    cur_text_tokens = [word]
                    prev_end = w_end
                else:
                    # continue chunk
                    cur_text_tokens.append(word)
                    prev_end = w_end

            # flush last chunk (if any tokens)
            if cur_text_tokens:
                out.append(TextSegment(
                    writer=str(cur_spk) if cur_spk is not None else None,
                    text=" ".join(cur_text_tokens).strip(),
                    start_time=cur_start if cur_start is not None else float(seg.get("start") or 0.0),
                    end_time=prev_end if prev_end is not None else float(seg.get("end") or seg.get("start") or 0.0),
                    language=language,
                ))

        for i in range(len(out)):
            out[i].text = " ".join(out[i].text.split())

        return out

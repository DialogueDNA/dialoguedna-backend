from __future__ import annotations
import os, threading
from typing import Dict, Any, Optional, Callable, cast

import torch
import torchaudio
from transformers import AutoModelForAudioClassification, AutoProcessor

from app.core.config.providers.hugging_face.superb import SuperbConfig
from app.interfaces.services.emotions import EmotionAnalyzerOutput
from app.interfaces.services.emotions.audio import (
    EmotionAudioAnalyzer,
    EmotionAnalyzerByAudioInput,
    EmotionAnalyzerByAudioOutput,
)


class SuperbAudioEmotionAnalyzer(EmotionAudioAnalyzer):
    def __init__(self, cfg: SuperbConfig):
        self._cfg = cfg
        self._lock = threading.Lock()
        self._proc: Optional[AutoProcessor] = None
        self._model: Optional[AutoModelForAudioClassification] = None
        self._id2label: Optional[Dict[int, str]] = None
        self._target_sr: Optional[int] = None
        os.makedirs(self._cfg.cache_dir, exist_ok=True)

    @torch.inference_mode()
    def analyze(self, segment: EmotionAnalyzerByAudioInput) -> EmotionAnalyzerByAudioOutput:
        self._ensure_model()

        # ---- load audio (path or tensor) ----
        audio_obj: Any = segment.audio
        if isinstance(audio_obj, torch.Tensor):
            if segment.sample_rate is None:
                raise ValueError("sample_rate must be provided when segment.audio is a Tensor")
            wf, sr = audio_obj, int(segment.sample_rate)
        else:
            wf, sr = torchaudio.load(str(audio_obj))

        # ---- crop ----
        start_sec = float(segment.start_time or 0.0)
        end_sec = float(segment.end_time if segment.end_time is not None else (wf.shape[-1] / sr))
        if end_sec < start_sec:
            end_sec = start_sec
        s_idx = max(0, int(round(start_sec * sr)))
        e_idx = min(wf.shape[-1], int(round(end_sec * sr)))
        if e_idx <= s_idx:
            e_idx = min(wf.shape[-1], s_idx + 1)
        wf = wf[:, s_idx:e_idx]

        # ---- mono & clamp ----
        if wf.dim() == 2 and wf.size(0) > 1:
            wf = wf.mean(dim=0, keepdim=True)
        elif wf.dim() == 1:
            wf = wf.unsqueeze(0)
        wf = wf.clamp_(-1.0, 1.0)

        # ---- resample to model SR ----
        target_sr = int(self._target_sr or sr)
        if sr != target_sr:
            wf = torchaudio.functional.resample(wf, sr, target_sr)
            sr = target_sr

        # ---- windowed inference (logits averaging) ----
        T = wf.shape[-1]
        chunk_len = max(int(self._cfg.window_sec * sr), sr // 2)
        hop = max(int(chunk_len * self._cfg.hop_fraction), 1)

        sum_logits = None
        n_windows = 0
        pos = 0
        proc: Callable[..., dict] = cast(Callable[..., dict], self._require_processor())
        model: torch.nn.Module = cast(torch.nn.Module, self._require_model())

        while pos < T:
            end = min(pos + chunk_len, T)
            chunk = wf[:, pos:end]
            if chunk.numel() == 0:
                break
            if chunk.shape[-1] == 0:
                chunk = wf[:, pos:pos+1]

            inputs = proc(chunk.squeeze(0).cpu().numpy(), sampling_rate=sr, return_tensors="pt")
            inputs = {k: v.to(self._cfg.device, non_blocking=True) for k, v in inputs.items()}

            logits = model(**inputs).logits  # [1, num_labels]
            sum_logits = logits if sum_logits is None else (sum_logits + logits)
            n_windows += 1

            if end == T:
                break
            pos += hop

        avg_logits = sum_logits / max(1, n_windows)
        probs = torch.softmax(avg_logits, dim=-1)[0]
        id2label = self._id2label or {i: str(i) for i in range(probs.numel())}
        emotions = {id2label[i]: float(probs[i]) for i in range(probs.numel())}
        return EmotionAnalyzerOutput(emotions_intensity_dict=emotions)

    # ---- internals ---------------------------------------------------------
    def _ensure_model(self) -> None:
        if self._model is not None and self._proc is not None:
            return
        with self._lock:
            if self._model is not None and self._proc is not None:
                return
            model_id = self._cfg.model
            self._proc = AutoProcessor.from_pretrained(model_id, cache_dir=self._cfg.cache_dir)
            self._model = AutoModelForAudioClassification.from_pretrained(model_id, cache_dir=self._cfg.cache_dir)
            self._model.to(self._cfg.device).eval()
            self._id2label = dict(self._model.config.id2label)
            # get expected sampling rate
            sr = getattr(self._proc, "sampling_rate", None)
            if sr is None and hasattr(self._proc, "feature_extractor"):
                sr = getattr(self._proc.feature_extractor, "sampling_rate", None)
            self._target_sr = int(sr or 16_000)

    def _require_model(self) -> AutoModelForAudioClassification:
        if self._model is None:
            raise RuntimeError("Model not loaded")
        return self._model

    def _require_processor(self) -> AutoProcessor:
        if self._proc is None:
            raise RuntimeError("Processor not loaded")
        return self._proc

from __future__ import annotations
import os
import threading
import logging
from typing import List, Optional

import torch
from speechbrain.inference.separation import SepformerSeparation

from app.core.config.providers.hugging_face.sepformer import SepformerConfig
from app.interfaces.services.audio.separator import (
    AudioSeparator,
    AudioSeparatorInput,
    AudioSeparatorOutput,
)

logger = logging.getLogger(__name__)


class SepformerSeparator(AudioSeparator):
    """
    Production-ready SepFormer separator with:
    - Lazy, thread-safe model init (heavy model; init once per process).
    - Device handling (CPU/CUDA) and no-grad inference.
    - Optional resampling to the model's sample rate and back.
    - Chunked overlap-add (OLA) to handle long audios without OOM.
    - Configurable downmix from multichannel input.

    Assumptions:
      - AudioSeparatorInput.waveform: torch.Tensor [C, T] or [T], float-ish in [-1, 1].
      - AudioSeparatorInput.sample_rate: int
      - AudioSeparatorOutput expects a list[Tensor[T]] in `separated_waveforms`.

    Notes:
      - Most public SepFormer checkpoints expect 16 kHz. If your input differs,
        we resample with linear interpolation (dependency-free, good quality for speech).
      - Number of output sources is defined by the checkpoint; if cfg.num_speakers is set,
        we trim or zero-pad to match.
    """

    def __init__(self, cfg: SepformerConfig):
        self._cfg = cfg
        self._sep: Optional[SepformerSeparation] = None
        self._lock = threading.Lock()

        # --- Config defaults (kept defensive to avoid breaking current configs) ---
        self._device: str = getattr(cfg, "device", "cpu")
        self._cache_dir: str = getattr(
            cfg,
            "cache_dir",
            os.path.join(os.path.expanduser("~"), ".cache", "speechbrain", "sepformer"),
        )
        self._model_sr: int = int(getattr(cfg, "model_sample_rate", 16_000))
        self._downmix_mode: str = getattr(cfg, "downmix_mode", "mean")  # "mean" | "left" | "right"
        self._chunk_sec: float = float(getattr(cfg, "chunk_sec", 12.0))  # chunk length in seconds
        self._hop_fraction: float = float(getattr(cfg, "hop_fraction", 0.5))  # 50% overlap
        self._num_speakers: Optional[int] = getattr(cfg, "num_speakers", None)

        os.makedirs(self._cache_dir, exist_ok=True)

    # ----------------------------
    # Public API
    # ----------------------------
    @torch.inference_mode()
    def separate(self, audio: AudioSeparatorInput) -> AudioSeparatorOutput:
        wf, sr = self._normalize_input(audio)
        device_in = wf.device
        dtype_in = wf.dtype

        # Downmix to mono as SepFormer expects a single-channel mixture
        mono = self._downmix_to_mono(wf)

        # Resample to model SR if needed
        if sr != self._model_sr:
            mono = self._resample_torch(mono, sr, self._model_sr)

        # Run chunked separation at model SR
        est_sources = self._separate_chunked(mono, self._model_sr)  # list[Tensor[T_model]]

        # Enforce num_speakers if configured (trim / pad with zeros)
        if self._num_speakers is not None:
            est_sources = self._conform_num_speakers(est_sources, self._num_speakers)

        # Resample each source back to original SR if needed
        if sr != self._model_sr:
            est_sources = [self._resample_torch(s.unsqueeze(0), self._model_sr, sr).squeeze(0) for s in est_sources]

        # Clamp very lightly to avoid inter-chunk numerical spikes
        est_sources = [s.clamp_(-1.0, 1.0).to(device_in, dtype=dtype_in, non_blocking=True) for s in est_sources]

        return AudioSeparatorOutput(separated_waveforms=est_sources)

    # ----------------------------
    # Core: model execution (chunked)
    # ----------------------------
    def _separate_chunked(self, mono: torch.Tensor, sr: int) -> List[torch.Tensor]:
        """
        Chunked overlap-add separation to reduce peak memory usage.
        Input:
          mono: [1, T] tensor at model SR
          sr:   sample rate (== self._model_sr)
        Returns:
          list[Tensor[T]] of estimated sources (all same length as input)
        """
        assert mono.dim() == 2 and mono.size(0) == 1, "Expected mono shape [1, T]"

        model = self._get_model()

        # Shapes and windowing
        T = mono.size(1)
        chunk_len = max(int(self._chunk_sec * sr), sr // 2)  # guard min size
        hop = max(int(chunk_len * self._hop_fraction), 1)
        if chunk_len >= T:
            # Single pass if audio is shorter than a chunk
            return self._run_model(model, mono)

        window = torch.hann_window(chunk_len, periodic=False, dtype=mono.dtype, device=mono.device)

        # We'll infer number of sources from the first forward
        # Allocate outputs lazily
        out_buffers: Optional[List[torch.Tensor]] = None
        weight = torch.zeros(T, dtype=mono.dtype, device=mono.device)

        # Iterate chunks with OLA
        start = 0
        while start < T:
            end = min(start + chunk_len, T)
            chunk = mono[:, start:end]

            # Pad last chunk to full size for stable model behavior
            pad_len = chunk_len - (end - start)
            if pad_len > 0:
                chunk = torch.nn.functional.pad(chunk, (0, pad_len))

            # Apply analysis window
            chunk = chunk * window.unsqueeze(0)

            # Forward
            chunk_sources = self._run_model(model, chunk)  # list[Tensor[T_chunk]]

            # Lazy buffer allocation
            if out_buffers is None:
                nsrc = len(chunk_sources)
                out_buffers = [torch.zeros(T, dtype=mono.dtype, device=mono.device) for _ in range(nsrc)]

            # Overlap-add with synthesis window
            for i, src_chunk in enumerate(chunk_sources):
                # Trim padding before OLA contribution
                valid = src_chunk[: end - start]
                out_buffers[i][start:end] += valid * window[: end - start]

            weight[start:end] += window[: end - start]

            start += hop

        # Normalize by window overlap weights to restore amplitude
        weight = torch.clamp(weight, min=1e-6)
        out = [buf / weight for buf in out_buffers]
        return out

    def _run_model(self, model: SepformerSeparation, mono_chunk: torch.Tensor) -> List[torch.Tensor]:
        """
        Runs SepFormer on a mono chunk and returns list of sources.
        Expected input shape: [1, T] at model SR.
        """
        # Move to model device if needed
        if self._device != str(mono_chunk.device):
            mono_chunk = mono_chunk.to(self._device, non_blocking=True)

        # Some SpeechBrain checkpoints expect [B, T], others accept [B, 1, T].
        # We'll try [B, T] first and fall back if needed.
        B, T = mono_chunk.shape
        assert B == 1, "Batching not supported here"

        try:
            out = model.separate_batch(mono_chunk)  # expect [B, nsrc, T]
        except Exception:
            out = model.separate_batch(mono_chunk.unsqueeze(1))  # [B, 1, T]

        # Convert to list[Tensor[T]] on the *input* device
        if isinstance(out, torch.Tensor) and out.dim() == 3:
            # [1, nsrc, T]
            out_list = [out[0, i, :].detach() for i in range(out.size(1))]
        elif isinstance(out, (list, tuple)) and len(out) > 0:
            # Some wrappers may return a list of [B, T]
            out_list = [o[0].detach() for o in out]
        else:
            raise RuntimeError("Unexpected SepFormer output shape/type.")

        # Back to the mono_chunk original device if the model moved it
        target_device = mono_chunk.device
        out_list = [o.to(target_device, non_blocking=True) for o in out_list]
        return out_list

    def _get_model(self) -> SepformerSeparation:
        """
        Lazy-load SepFormer once, thread-safe. Heavy op; avoid doing this per call.
        """
        if self._sep is not None:
            return self._sep
        with self._lock:
            if self._sep is None:
                logger.info("Loading SepFormer model '%s' on %s", self._cfg.model, self._device)
                self._sep = SepformerSeparation.from_hparams(
                    source=self._cfg.model,
                    savedir=self._cache_dir,
                    run_opts={"device": self._device},
                )
        return self._sep

    # ----------------------------
    # Utilities
    # ----------------------------
    @staticmethod
    def _normalize_input(audio: AudioSeparatorInput) -> tuple[torch.Tensor, int]:
        """
        Ensures waveform is float tensor shaped [C, T] on its current device.
        Returns (waveform, sample_rate).
        """
        wf = audio.audio
        if wf.dim() == 1:
            wf = wf.unsqueeze(0)  # [1, T]
        assert wf.dim() == 2, "waveform must be [C, T] or [T]"
        sr = int(getattr(audio, "sample_rate", 16_000))
        return wf, sr

    def _downmix_to_mono(self, wf: torch.Tensor) -> torch.Tensor:
        """
        Downmix multi-channel to mono according to config.
        Returns shape [1, T].
        """
        if wf.size(0) == 1:
            return wf

        mode = (self._downmix_mode or "mean").lower()
        if mode == "left":
            mono = wf[0:1, :]
        elif mode == "right":
            mono = wf[-1:, :]
        else:
            mono = wf.mean(dim=0, keepdim=True)
        # Keep safe range
        return mono.clamp_(-1.0, 1.0)

    @staticmethod
    def _resample_torch(wf: torch.Tensor, src_sr: int, dst_sr: int) -> torch.Tensor:
        """
        Dependency-free linear interpolation resampler (good for speech).
        Input:  [1, t_src]  Output: [1, t_dst]
        """
        if src_sr == dst_sr:
            return wf
        assert wf.dim() == 2 and wf.size(0) == 1, "resampler expects [1, T]"
        t_src = wf.size(1)
        t_dst = max(int(round(t_src * (dst_sr / float(src_sr)))), 1)
        # Create normalized time axes
        x_src = torch.linspace(0.0, 1.0, steps=t_src, device=wf.device, dtype=wf.dtype)
        x_dst = torch.linspace(0.0, 1.0, steps=t_dst, device=wf.device, dtype=wf.dtype)
        # Interpolate per-channel (mono)
        out = torch.interp(x_dst, x_src, wf[0])
        return out.unsqueeze(0)

    @staticmethod
    def _conform_num_speakers(sources: List[torch.Tensor], n: int) -> List[torch.Tensor]:
        """
        Trim or zero-pad the list of separated sources to exactly n signals.
        """
        if n <= 0:
            return sources
        if len(sources) == n:
            return sources
        if len(sources) > n:
            return sources[:n]
        # pad
        t = sources[0].size(0)
        pad_count = n - len(sources)
        zeros = [torch.zeros(t, dtype=sources[0].dtype, device=sources[0].device) for _ in range(pad_count)]
        return sources + zeros

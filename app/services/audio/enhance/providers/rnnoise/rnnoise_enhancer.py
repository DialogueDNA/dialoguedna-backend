from __future__ import annotations
from typing import Literal, Dict

import numpy as np
import torch
from pyrnnoise import RNNoise

from app.core.config.providers.rnnoise import RNNoiseConfig
from app.interfaces.services.audio.enhancer import (
    AudioEnhancer,
    AudioEnhancerInput,
    AudioEnhancerOutput,
)

StrengthT = Literal["light", "medium", "strong"]


class RNNoiseEnhancer(AudioEnhancer):
    """
    Offline RNNoise-based denoiser.

    Design:
      - RNNoise is stateful across frames -> create a fresh instance *per channel per call*
        to avoid cross-request state leakage and ensure thread-safety.
      - RNNoise expects ~48 kHz input. If needed, we resample to `cfg.target_sample_rate`
        and resample back to the original rate after denoising.
      - Multi-channel audio is processed per-channel independently and re-stacked.

    Input expectations:
      - AudioEnhancerInput.waveform: torch.Tensor of shape [C, T] or [T], float in ~[-1, 1]
      - AudioEnhancerInput.sample_rate: int
    """

    def __init__(self, cfg: RNNoiseConfig):
        self._cfg = cfg
        self._passes_by_strength: Dict[StrengthT, int] = {
            "light": cfg.passes_light,
            "medium": cfg.passes_medium,
            "strong": cfg.passes_strong,
        }

    @torch.inference_mode()
    def enhance(self, audio: AudioEnhancerInput) -> AudioEnhancerOutput:
        # ---- Normalize input shape/dtype ----
        wf = audio.audio
        if wf.dim() == 1:
            wf = wf.unsqueeze(0)  # [1, T]
        assert wf.dim() == 2, "waveform must be [C, T] or [T]"
        orig_sr: int = int(getattr(audio, "sample_rate", self._cfg.target_sample_rate))
        device = wf.device
        in_dtype = wf.dtype

        # -> numpy float32 on CPU
        wf_np = wf.detach().to(torch.float32).cpu().numpy()  # [C, T]

        # ---- Resample to RNNoise SR if needed ----
        target_sr = int(self._cfg.target_sample_rate)
        if self._cfg.enable_resample and orig_sr != target_sr:
            wf_proc = self._resample_np(wf_np, orig_sr, target_sr)
        else:
            wf_proc = wf_np

        # Keep safe amplitude range
        np.clip(wf_proc, -1.0, 1.0, out=wf_proc)

        # ---- Denoise per channel with fresh RNNoise instances ----
        strength: StrengthT = getattr(self._cfg, "enhancer_strength", "medium")
        num_passes = max(1, int(self._passes_by_strength.get(strength, 2)))

        denoised_list = []
        for c in range(wf_proc.shape[0]):
            x = wf_proc[c]  # [T]
            # New RNNoise per channel to avoid leaking state across requests
            rn = RNNoise(sample_rate=target_sr)
            y = x[np.newaxis, :]  # [1, T] as expected by wrapper
            for _ in range(num_passes):
                y = rn.denoise_chunk(y)  # returns [1, T]
            denoised_list.append(np.squeeze(y, axis=0))  # -> [T]

        denoised_np = np.stack(denoised_list, axis=0)  # [C, T_target]

        # ---- Resample back to original SR if needed ----
        if self._cfg.enable_resample and orig_sr != target_sr:
            denoised_np = self._resample_np(denoised_np, target_sr, orig_sr)

        if self._cfg.clamp_after:
            np.clip(denoised_np, -1.0, 1.0, out=denoised_np)

        enhanced = torch.from_numpy(denoised_np).to(device=device, dtype=in_dtype, non_blocking=True)
        return AudioEnhancerOutput(enhanced_audio=enhanced)

    # ----------------------------
    # Utilities
    # ----------------------------
    @staticmethod
    def _resample_np(wf: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
        """
        Lightweight per-channel linear resampler to avoid extra deps.
        Input:  [c, t_src]  Output: [c, t_dst]
        For highest fidelity you may swap with torchaudio/kornia later.
        """
        if src_sr == dst_sr:
            return wf
        c, t_src = wf.shape
        t_dst = max(int(round(t_src * (dst_sr / float(src_sr)))), 1)

        x_src = np.linspace(0.0, 1.0, num=t_src, endpoint=False, dtype=np.float64)
        x_dst = np.linspace(0.0, 1.0, num=t_dst, endpoint=False, dtype=np.float64)
        out = np.empty((c, t_dst), dtype=wf.dtype)
        for ch in range(c):
            out[ch] = np.interp(x_dst, x_src, wf[ch].astype(np.float64)).astype(wf.dtype)
        return out

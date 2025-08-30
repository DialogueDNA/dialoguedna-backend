from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Union, Any

import torch
import torchaudio
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

from app.core.config import (
    TONE_EMOTION_MODEL,
    TONE_DEVICE,
    TONE_WINDOW_SEC,
    TONE_HOP_FRACTION,
    SAMPLE_RATE,
)


@dataclass
class AudioSegment:
    audio: Union[str, torch.Tensor]
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    sample_rate: Optional[int] = None


@dataclass
class ToneEmotionResult:
    emotions_intensity_dict: Dict[str, float]
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class SuperbToneEmotionAnalyzer:
    def __init__(
        self,
        model_id: str = TONE_EMOTION_MODEL,
        device: str = TONE_DEVICE,
        cache_dir: str = ".hf_cache",
        window_sec: float = TONE_WINDOW_SEC,
        hop_fraction: float = TONE_HOP_FRACTION,
    ):
        # Resolve device safely
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
        self._device_str = device
        self._device = torch.device(device)

        # Load feature extractor + model (ללא tokenizer)
        self._fe = AutoFeatureExtractor.from_pretrained(model_id, cache_dir=cache_dir)
        self._model = (
            AutoModelForAudioClassification.from_pretrained(model_id, cache_dir=cache_dir)
            .to(self._device)
            .eval()
        )

        # Labels map
        self._id2label = dict(self._model.config.id2label)

        # Target sample rate from extractor (fallback ל-SAMPLE_RATE)
        self._target_sr = getattr(self._fe, "sampling_rate", SAMPLE_RATE or 16000)

        # Windowing params
        self._window_sec = float(window_sec)
        self._hop_fraction = float(hop_fraction)

    @torch.inference_mode()
    def analyze(self, seg: AudioSegment) -> ToneEmotionResult:
        audio_obj: Any = seg.audio

        # Load waveform + sr
        if isinstance(audio_obj, torch.Tensor):
            if seg.sample_rate is None:
                raise ValueError("sample_rate must be provided when audio is a Tensor")
            wf, sr = audio_obj.detach().cpu(), int(seg.sample_rate)
            if wf.dim() == 1:
                wf = wf.unsqueeze(0)
        else:
            wf, sr = torchaudio.load(str(audio_obj))  # (C, T)

        # Crop to [start_time, end_time]
        s = float(seg.start_time or 0.0)
        e = float(seg.end_time or (wf.shape[-1] / sr))
        a = max(0, int(round(s * sr)))
        b = max(a + 1, min(wf.shape[-1], int(round(e * sr))))
        wf = wf[:, a:b]

        # Mono
        if wf.dim() == 2 and wf.size(0) > 1:
            wf = wf.mean(0, keepdim=True)
        elif wf.dim() == 1:
            wf = wf.unsqueeze(0)

        # Clamp
        wf = wf.clamp_(-1.0, 1.0)

        # Resample if needed
        if sr != self._target_sr:
            wf = torchaudio.functional.resample(wf, sr, self._target_sr)
            sr = self._target_sr

        T = wf.shape[-1]
        chunk_len = max(int(self._window_sec * sr), sr // 2)
        hop = max(int(chunk_len * self._hop_fraction), 1)

        sum_logits = None
        n = 0
        pos = 0

        while pos < T:
            end = min(pos + chunk_len, T)
            x = wf[:, pos:end]
            if x.numel() == 0:
                break
            if x.shape[-1] == 0:
                x = wf[:, pos : pos + 1]

            # Feature extractor → inputs
            inputs = self._fe(
                x.squeeze(0).cpu().numpy(),
                sampling_rate=sr,
                return_tensors="pt",
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            logits = self._model(**inputs).logits  # (1, num_labels)
            sum_logits = logits if sum_logits is None else (sum_logits + logits)
            n += 1

            if end == T:
                break
            pos += hop

        # Softmax over averaged logits
        probs = torch.softmax(sum_logits / max(1, n), dim=-1)[0]
        emotions = {self._id2label[i]: float(probs[i]) for i in range(probs.numel())}

        return ToneEmotionResult(
            emotions_intensity_dict=emotions,
            start_time=seg.start_time,
            end_time=seg.end_time,
        )

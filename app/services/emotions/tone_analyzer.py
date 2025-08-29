from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Union, Any

import torch
import torchaudio
from transformers import AutoModelForAudioClassification, AutoProcessor
from app.core.config import (
    TONE_EMOTION_MODEL,
    TONE_DEVICE,
    TONE_WINDOW_SEC,
    TONE_HOP_FRACTION,
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
    def __init__(self, model_id: str = TONE_EMOTION_MODEL, device: str = TONE_DEVICE,
                 cache_dir: str = ".hf_cache", window_sec: float = TONE_WINDOW_SEC, hop_fraction: float = TONE_HOP_FRACTION):
        self._device = device
        self._proc = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
        self._model = AutoModelForAudioClassification.from_pretrained(model_id, cache_dir=cache_dir).to(device).eval()
        self._id2label = dict(self._model.config.id2label)
        self._target_sr = getattr(self._proc, "sampling_rate", 16000)
        self._window_sec = window_sec
        self._hop_fraction = hop_fraction

    @torch.inference_mode()
    def analyze(self, seg: AudioSegment) -> ToneEmotionResult:
        audio_obj: Any = seg.audio
        if isinstance(audio_obj, torch.Tensor):
            if seg.sample_rate is None:
                raise ValueError("sample_rate must be provided when audio is a Tensor")
            wf, sr = audio_obj.detach().cpu(), int(seg.sample_rate)
        else:
            wf, sr = torchaudio.load(str(audio_obj))

        s = float(seg.start_time or 0.0)
        e = float(seg.end_time or (wf.shape[-1] / sr))
        a = max(0, int(round(s * sr)))
        b = max(a + 1, min(wf.shape[-1], int(round(e * sr))))
        wf = wf[:, a:b]

        if wf.dim() == 2 and wf.size(0) > 1:
            wf = wf.mean(0, keepdim=True)
        elif wf.dim() == 1:
            wf = wf.unsqueeze(0)
        wf = wf.clamp_(-1.0, 1.0)

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
                x = wf[:, pos:pos + 1]
            inputs = self._proc(x.squeeze(0).cpu().numpy(), sampling_rate=sr, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            logits = self._model(**inputs).logits
            sum_logits = logits if sum_logits is None else (sum_logits + logits)
            n += 1
            if end == T:
                break
            pos += hop

        probs = torch.softmax(sum_logits / max(1, n), dim=-1)[0]
        emotions = {self._id2label[i]: float(probs[i]) for i in range(probs.numel())}
        return ToneEmotionResult(emotions_intensity_dict=emotions, start_time=seg.start_time, end_time=seg.end_time)





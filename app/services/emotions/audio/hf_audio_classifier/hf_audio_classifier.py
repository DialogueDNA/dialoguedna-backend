from __future__ import annotations
from typing import List, Dict
import torch, torchaudio
from transformers import AutoModelForAudioClassification, Wav2Vec2FeatureExtractor

from app.ports.services.emotions.audio_analyzer import AudioEmotionAnalyzer


class HFAudioClassifier(AudioEmotionAnalyzer):
    """
    Hugging Face audio classifier for speech emotion recognition.
    Conforms to AudioEmotionAnalyzer (analyze_audio_file / analyze_audio_blob).
    """
    def __init__(self, model_name: str, target_sr: int = 16000):
        self._fe = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        self._model = AutoModelForAudioClassification.from_pretrained(model_name)
        self._id2label = self._model.config.id2label
        self._target_sr = target_sr

    def _classify_chunk(self, wav: torch.Tensor, sr: int) -> Dict[str, float]:
        if wav.dim() == 2 and wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)
        if sr != self._target_sr:
            wav = torchaudio.functional.resample(wav, sr, self._target_sr)
            sr = self._target_sr
        inputs = self._fe(wav.squeeze(), sampling_rate=sr, return_tensors="pt")
        with torch.no_grad():
            logits = self._model(**inputs).logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        return {self._id2label[i]: float(probs[i]) for i in range(len(probs))}

    def analyze(self, segments: List[AudioSegmentInput]) -> List[AudioSegmentOutput]:
        # Each segment["audio"] is a path; cut by (start_time, end_time) and classify
        out: List[AudioSegmentOutput] = []
        for seg in segments:
            path = seg["audio"]
            wav, sr = torchaudio.load(path)
            s_idx = int(max(0.0, seg["start_time"]) * sr)
            e_idx = int(max(seg["start_time"], seg["end_time"]) * sr)
            chunk = wav[:, s_idx:e_idx] if e_idx > s_idx else wav[:, s_idx:s_idx+1]
            scores = self._classify_chunk(chunk, sr)
            out.append({
                "speaker": seg["speaker"],
                "audio": path,
                "start_time": float(seg["start_time"]),
                "end_time": float(seg["end_time"]),
                "emotions": scores
            })
        return out

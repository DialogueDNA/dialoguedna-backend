# audio_pipeline/audio_emotion_model.py

import torch
import torchaudio
from transformers import AutoModelForAudioClassification, Wav2Vec2FeatureExtractor
from typing import Dict

class AudioEmotionModel:
    def __init__(self, model_name: str = "superb/hubert-large-superb-er"):
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        self.model = AutoModelForAudioClassification.from_pretrained(model_name)
        self.label_mapping = self.model.config.id2label

    def analyze(self, file_path: str) -> Dict[str, float]:
        waveform, sr = torchaudio.load(file_path)
        if sr != 16000:
            waveform = torchaudio.functional.resample(waveform, sr, 16000)
            sr = 16000

        inputs = self.feature_extractor(waveform.squeeze(), sampling_rate=sr, return_tensors="pt")
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]

        return {
            self.label_mapping[i]: float(probs[i])
            for i in range(len(probs))
        }

    def get_top_emotion(self, file_path: str) -> str:
        scores = self.analyze(file_path)
        return max(scores.items(), key=lambda x: x[1])[0]

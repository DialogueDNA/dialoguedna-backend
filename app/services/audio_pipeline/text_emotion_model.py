# audio_pipeline/text_emotion_model.py

from transformers import pipeline
from typing import Dict

class TextEmotionModel:
    def __init__(self, model_name: str = "j-hartmann/emotion-english-distilroberta-base"):
        self.model = pipeline("text-classification", model=model_name, return_all_scores=True)

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Returns: {label: score}
        """
        predictions = self.model(text[:512])[0]  # max 512 tokens
        return {p["label"]: p["score"] for p in predictions}

    def get_top_emotion(self, text: str) -> str:
        scores = self.analyze(text)
        return max(scores.items(), key=lambda x: x[1])[0]

# summarizer_engine.py

from typing import List, Dict
from openai import AzureOpenAI, RateLimitError
from app.core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
)
import time

class SummarizerEngine:
    def __init__(self, emotion_threshold: float = 0.7):
        self.emotion_threshold = emotion_threshold
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )

    def summarize(self, annotated_sentences: List[Dict]) -> str:
        descriptive_lines = []
        for entry in annotated_sentences:
            emotions = entry.get("emotions", [])
            if not emotions:
                continue
            top = max(emotions, key=lambda e: e["score"])
            if top["score"] >= self.emotion_threshold:
                descriptive_lines.append(
                    f'{entry["speaker"]} said: "{entry["text"]}" — emotion detected: **{top["label"].lower()}** ({round(top["score"]*100, 2)}%)'
                )

        prompt_text = "\n".join(descriptive_lines)

        prompt = (
            "You are a sensitive and experienced journalist and conversation analyst.\n"
            "You've received a transcript with speaker labels and emotional tags for each sentence.\n\n"
            "Your task is to write a fluent, emotionally intelligent, and human-centered summary of the conversation.\n"
            "Include subheadings (e.g., 🎬 Beginning / 👩‍👧 Talking about family / 😂 Jokes and Humor), reflect on emotions, personal dynamics, and turning points.\n"
            "Write with depth, insight, and elegance. You may interpret how the speakers felt, what affected them, and why certain parts were humorous, exhausting, or touching.\n"
            "Emphasize powerful or touching lines using **bold**, and don't list emotion percentages.\n"
            "You are telling a human story — not generating analytics."
        )

        retries = 3
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": prompt_text}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                break
            except RateLimitError:
                print(f"⚠️ Rate limit hit (attempt {attempt+1}/{retries}). Waiting 60 seconds...")
                time.sleep(60)
        else:
            raise RuntimeError("❌ Failed after 3 retries due to rate limiting.")

        return response.choices[0].message.content.strip()

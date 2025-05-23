"""
summarizer_engine.py

SummarizerEngine – generates emotionally insightful summaries from annotated text.

Responsibilities:
- Accept list of sentences with speaker and emotion annotations
- Format them into descriptive lines
- Use Azure OpenAI to generate a human-like emotional summary
- Return the summary as text (optionally save to file)

Note:
This replaces the file-based SummaryManager with a more flexible service component.
"""

from typing import List, Dict
from openai import AzureOpenAI, RateLimitError
from app.core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
)
import time
from pathlib import Path

class SummarizerEngine:
    def __init__(self, output_dir: Path = None, emotion_threshold: float = 0.7):
        self.output_dir = output_dir
        self.emotion_threshold = emotion_threshold
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )

    def summarize(self, annotated_sentences: List[Dict]) -> str:
        """
        Generate emotional summary from annotated sentences.

        :param annotated_sentences: List of {"speaker", "text", "emotions": [...] }
        :return: Summary string (and optionally save to markdown)
        """
        # Build descriptive prompt from annotated lines
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

        summary = response.choices[0].message.content.strip()

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            summary_path = self.output_dir / "conversation_summary.md"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"📝 Summary saved to: {summary_path}")

        return summary

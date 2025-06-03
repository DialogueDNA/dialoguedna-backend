"""
summarizer.py

Summarizer service – wraps SummarizerEngine to generate emotional summaries.

Responsibilities:
- Accept transcription text, emotion data, and speaker list
- Flatten the data into a sentence-level annotated list
- Delegate summarization to SummarizerEngine (Azure OpenAI)
- Return the summary text
"""

from typing import Any
from openai import AzureOpenAI, RateLimitError
from app.core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
)
import time


class Summarizer:
    def __init__(self, emotion_threshold: float = 0.7):
        self.emotion_threshold = emotion_threshold
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )

    def summarize(self, transcript: list[dict[str, Any]], emotions: list[dict[str, Any]]) -> str:
        """
        Generate emotional summary from annotated sentences.

        :param annotated_sentences: List of {"speaker", "text", "emotions": [...] }
        :return: Summary string (and optionally save to markdown)
        """

        annotated_sentences = self.annotate_emotional_transcript(transcript, emotions)

        # Build descriptive prompt from annotated lines
        descriptive_lines = []
        for entry in annotated_sentences:
            emotions = entry.get("emotions", [])

            if not isinstance(emotions, list) or not all(isinstance(e, dict) and "score" in e for e in emotions):
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

        return summary

    def annotate_emotional_transcript(
            self,
            transcript: list[dict[str, Any]],
            emotions: list[dict[str, Any]]
    ) -> list[dict]:
        """
        Annotate a transcript with corresponding emotional analysis.

        Assumes both `transcript` and `emotions` are lists of the same length and order.

        :param transcript: List of { speaker, text, start_time, end_time }
        :param emotions: List of { speaker, text, emotions }
        :return: Annotated transcript: List of { speaker, text, start_time, end_time, emotions }
        """
        if len(transcript) != len(emotions):
            raise ValueError("Transcript and emotions lists must be the same length.")

        annotated = []

        for i in range(len(transcript)):
            annotated.append({
                "speaker": transcript[i].get("speaker", "?"),
                "text": transcript[i].get("text", ""),
                "start_time": transcript[i].get("start_time", None),
                "end_time": transcript[i].get("end_time", None),
                "emotions": emotions[i].get("emotions", [])
            })

        print(annotated)

        return annotated
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
from difflib import SequenceMatcher
from app.services.summary.prompts import PROMPT_PRESETS, PromptStyle
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

    def summarize(self, transcript: list[dict[str, Any]], emotions: list[dict[str, Any]], preset_key: PromptStyle) -> str:
        """
        Generate an emotional summary from a transcript and emotion annotations.

        Args:
            transcript: List of dicts with keys {speaker, text, start_time, end_time}
            emotions: List of dicts with keys {emotions: [{label, score}, ...]}
            preset_key: A string key from PROMPT_PRESETS indicating the desired summary style

        Returns:
            A string containing the generated summary.
        """


        #annotated_sentences = self.annotate_emotional_transcript(transcript, emotions)
        annotated_sentences = self.annotate_by_matching(transcript, emotions)

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



        prompt = PROMPT_PRESETS.get(preset_key.value)

        if prompt is None:
            raise ValueError(f"Invalid prompt preset key: {preset_key}")


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

    def annotate_by_matching(
            self,
            transcript: list[dict[str, Any]],
            emotions: list[dict[str, Any]],
            time_threshold: float = 0.05,
            similarity_threshold: float = 0.95
    ) -> list[dict[str, Any]]:
        """
        Annotate a transcript by matching each sentence to emotion data based on text and timestamp similarity.

        :param transcript: List of {speaker, text, start_time, end_time}
        :param emotions: List of {speaker, text, start_time, emotions}
        :param time_threshold: Max allowed time difference in seconds
        :param similarity_threshold: Minimum required text similarity ratio (0–1)
        :return: List of annotated sentences with emotions
        """
        annotated = []

        for t in transcript:
            match = None
            for e in emotions:
                time_match = abs(float(t["start_time"]) - float(e["start_time"])) <= time_threshold
                text_match = SequenceMatcher(None, t["text"].strip(), e["text"].strip()).ratio() >= similarity_threshold

                if time_match and text_match:
                    match = e
                    break

            annotated.append({
                "speaker": t.get("speaker", "?"),
                "text": t.get("text", ""),
                "start_time": t.get("start_time"),
                "end_time": t.get("end_time"),
                "emotions": match.get("emotions", []) if match else []
            })

        return annotated
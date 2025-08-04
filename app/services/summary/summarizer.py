from typing import Any
from openai import AzureOpenAI, RateLimitError
from difflib import SequenceMatcher
from app.services.summary.prompts import PROMPT_PRESETS, PromptStyle
from app.services.summary.prompts import PROMPT_LABELS  # new
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
        annotated_sentences = self.annotate_by_matching(transcript, emotions)

        descriptive_lines = []
        for entry in annotated_sentences:
            emotion_list = entry.get("emotions", [])
            if not isinstance(emotion_list, list):
                continue

            strong_emotions = [e for e in emotion_list if isinstance(e, dict) and e.get("score", 0) >= self.emotion_threshold]
            if not strong_emotions:
                continue

            # Choose top emotion from filtered list
            top = max(strong_emotions, key=lambda e: e["score"])

            if preset_key in {PromptStyle.EMOTIONAL_STORY, PromptStyle.ALL_IN_ONE}:
                descriptive_lines.append(f'**Speaker {entry["speaker"]} ({top["label"].lower()})**: "{entry["text"]}"')
            elif preset_key == PromptStyle.PER_SPEAKER:
                descriptive_lines.append(f'Speaker {entry["speaker"]}: "{entry["text"]}"  \\ Emotion: **{top["label"]}**')
            elif preset_key == PromptStyle.ANALYTICAL:
                descriptive_lines.append(f'- Speaker {entry["speaker"]} | Emotion: {top["label"]} ({round(top["score"]*100)}%) | "{entry["text"]}"')
            else:
                descriptive_lines.append(f'{entry["speaker"]} said: "{entry["text"]}" — emotion detected: **{top["label"].lower()}** ({round(top["score"]*100, 2)}%)')

        prompt_text = "\n".join(descriptive_lines)
        prompt_data = PROMPT_PRESETS.get(preset_key.value)

        if prompt_data is None:
            raise ValueError(f"Invalid prompt preset key: {preset_key}")

        # Support both string and dict-based prompts
        if isinstance(prompt_data, dict):
            system_prompt = prompt_data.get("system", "You are a helpful assistant.")
            user_prompt = prompt_data.get("format", "{lines}").format(lines=prompt_text)
        else:
            system_prompt = prompt_data
            user_prompt = prompt_text

        retries = 3
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
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

        if not summary:
            raise ValueError("❌ GPT returned an empty summary.")

        return summary

    def annotate_by_matching(
            self,
            transcript: list[dict[str, Any]],
            emotions: list[dict[str, Any]],
            time_threshold: float = 0.05,
            similarity_threshold: float = 0.95
    ) -> list[dict[str, Any]]:
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

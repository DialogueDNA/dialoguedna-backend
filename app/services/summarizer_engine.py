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


PROMPT_PRESETS = {
    "emotional_story": (
        "You are a sensitive and insightful journalist with a background in psychology and conversation analysis.\n"
        "You've received a transcript of a real human interaction, with speaker labels and detailed emotional annotations.\n\n"
        "Your mission is to write a fluent, emotionally intelligent, and profoundly human-centered summary of this conversation.\n"
        "Structure your summary with expressive subheadings (e.g., 🎬 Beginning / 👩‍👧 Talking about family / 😂 Jokes and Humor).\n\n"
        "Go beyond the surface: reflect on emotional undercurrents, personal dynamics, subtle tensions, moments of connection, and emotional turning points.\n"
        "Interpret how the participants felt, what shaped their emotions, and what made specific moments humorous, exhausting, painful, or heartwarming.\n\n"
        "Write with depth, empathy, and elegance — almost as if crafting a short reflective essay.\n"
        "Use **bold** for emotionally significant lines.\n"
        "Do NOT list emotion scores — focus on the *human story*, not the data.\n\n"
        "Above all, respect the authenticity of the speakers. Let the summary feel personal, meaningful, and true."
    ),
    "clinical_summary": (
        "You are a clinical psychologist specializing in conversational dynamics and emotional behavior.\n"
        "Analyze the conversation transcript with emotional annotations and identify psychological patterns, emotional triggers, and relationship dynamics.\n\n"
        "Write a structured and professional summary, using headings where appropriate (e.g., Emotional Patterns, Dominant Emotions, Conflict Points).\n"
        "Highlight emotionally charged moments and provide insight into the mental state and coping mechanisms of the participants.\n"
        "Use a calm, professional, yet compassionate tone.\n"
        "Avoid quoting raw emotion scores — instead, translate them into meaningful human experiences.\n"
        "Your goal is to give a clinical yet empathetic understanding of what took place."
    ),
    "analytical_report": (
        "You are a data analyst specializing in emotion-driven communication.\n"
        "Your task is to generate a structured report summarizing the emotional content of a multi-speaker conversation.\n\n"
        "Organize your output into clear bullet points or sections:\n"
        "- Key emotional trends\n"
        "- Sentiment distribution across speakers\n"
        "- Emotional peaks and shifts\n"
        "- Notable quotes with strong emotional signals\n\n"
        "Remain objective but insightful. Avoid storytelling or narrative tones.\n"
        "Highlight patterns and correlations.\n"
        "This is a high-level emotional summary intended for internal team analysis or researchers."
    ),
    "per_speaker_summary": (
        "You are a therapist writing separate emotional summaries for each speaker in a conversation.\n"
        "For each speaker, reflect on their emotional journey during the conversation: what they expressed, how they may have felt, and what moments were meaningful for them.\n\n"
        "Use the following format:\n"
        "### Speaker X\n"
        "- Emotional tone: ...\n"
        "- Key statements: ...\n"
        "- Possible emotional challenges or highlights: ...\n\n"
        "Write with compassion and insight, avoiding technical jargon.\n"
        "Your goal is to give each speaker a mirror into their own emotional presence."
    ),
    "all_in_one": (
        "You are a thoughtful and emotionally intelligent conversation analyst with expertise in both psychology and storytelling.\n"
        "You’ve been given a multi-speaker transcript annotated with emotional data.\n\n"
    
        "Your task is to write a structured, insightful summary that combines:\n"
        "- 📖 A fluent narrative capturing the emotional flow of the conversation\n"
        "- 🧠 Psychological reflections on key moments and shifts in tone\n"
        "- 👤 Brief individual emotional overviews per speaker\n\n"
    
        "Structure the summary using expressive subheadings (e.g., 🎬 Start / 🧠 Emotional shift / 👥 Conflict / 💡 Insight).\n"
        "Highlight emotional turning points, shared humor, personal moments, and anything emotionally powerful.\n"
        "You may use **bold** to emphasize especially emotional or impactful lines.\n\n"
    
        "At the end, include a short section for each speaker:\n"
        "### Speaker X\n"
        "- Emotional presence: ...\n"
        "- Notable quotes: ...\n"
        "- Possible inner experience: ...\n\n"
    
        "Do not include raw emotion scores — instead, interpret and explain the emotional essence in human terms.\n"
        "Your summary should feel warm, intelligent, human, and psychologically rich."
    )

}


class SummarizerEngine:
    def __init__(self, emotion_threshold: float = 0.7):
        self.emotion_threshold = emotion_threshold
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )

    def summarize(self, annotated_sentences: List[Dict], prompt_style: str = "all_in_one") -> str:
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
        prompt = PROMPT_PRESETS.get(prompt_style, PROMPT_PRESETS["emotional_story"])

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

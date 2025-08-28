from typing import Any, List, Dict, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
from openai import AzureOpenAI, RateLimitError, APIError
from difflib import SequenceMatcher
from app.services.summary.prompts import PROMPT_PRESETS, PromptStyle
from app.services.summary.prompts import PROMPT_LABELS  # (לא בשימוש כאן, נשאר ל-UI)
from app.core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
)
import time, json, re


class SummaryResult(BaseModel):
    """
    A structured summary result for UI/DB/tests.
    """
    style: str
    summary_text: str
    descriptive_lines: List[str] = Field(default_factory=list)
    sections: Dict[str, str] = Field(default_factory=dict)           # e.g., {"🧭 1) Call Topic": "..."}
    action_items: List[Dict[str, str]] = Field(default_factory=list)  # [{"ID","Task","Owner","Due Date"}]
    retries: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Summarizer:
    """
    Summarizes a multi-speaker transcript using Azure OpenAI, guided by prompt presets.

    Stage 1: readability, safer errors, configurable temperature/max_tokens.
    Stage 2: add summarize_structured(...) + gentle parsers, without breaking backward compatibility.
    """

    def __init__(self, emotion_threshold: float = 0.7, temperature: float = 0.7, max_tokens: int = 1500):
        self.emotion_threshold = float(emotion_threshold)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )

    # ---------------- Public API ----------------

    def summarize(
        self,
        transcript: List[Dict[str, Any]],
        emotions: List[Dict[str, Any]],
        preset_key: PromptStyle
    ) -> str:
        """
        Backward-compatible path: returns plain text (string) exactly like before.
        """
        annotated_sentences = self.annotate_by_matching(transcript, emotions)
        descriptive_lines = self._build_descriptive_lines(annotated_sentences, preset_key)
        system_prompt, user_prompt = self._build_prompts(descriptive_lines, preset_key)
        text, attempts = self._call_gpt(system_prompt, user_prompt)
        text = (text or "").strip()
        if not text:
            raise ValueError("❌ GPT returned an empty summary.")
        return text

    def summarize_structured(
        self,
        transcript: List[Dict[str, Any]],
        emotions: List[Dict[str, Any]],
        preset_key: PromptStyle
    ) -> SummaryResult:
        """
        Structured path: returns SummaryResult with sections/action_items when possible,
        while still keeping the raw summary text intact.
        """
        annotated_sentences = self.annotate_by_matching(transcript, emotions)
        descriptive_lines = self._build_descriptive_lines(annotated_sentences, preset_key)
        system_prompt, user_prompt = self._build_prompts(descriptive_lines, preset_key)
        raw_text, attempts = self._call_gpt(system_prompt, user_prompt)
        raw_text = (raw_text or "").strip()
        if not raw_text:
            raise ValueError("❌ GPT returned an empty summary.")

        # Gentle parsing: sections, action items, JSON (if present)
        sections = self._extract_sections(raw_text)
        action_items = self._extract_action_items_from_html(raw_text)
        json_payload = self._extract_json(raw_text)
        if json_payload:
            sections = json_payload.get("sections", sections) or sections
            action_items = json_payload.get("action_items", action_items) or action_items

        try:
            return SummaryResult(
                style=preset_key.value,
                summary_text=raw_text,
                descriptive_lines=descriptive_lines,
                sections=sections,
                action_items=action_items,
                retries=attempts,
                metadata={"token_limit": self.max_tokens, "temperature": self.temperature},
            )
        except ValidationError:
            # Extremely defensive fallback
            return SummaryResult(style=preset_key.value, summary_text=raw_text)

    # ---------------- Internals ----------------

    def _build_prompts(self, descriptive_lines: List[str], preset_key: PromptStyle) -> Tuple[str, str]:
        """
        Compose system + user prompts from PROMPT_PRESETS and the descriptive lines.
        """
        prompt_data = PROMPT_PRESETS.get(preset_key.value)
        if not prompt_data:
            raise ValueError(f"Invalid prompt preset key: {preset_key}")

        lines_text = "\n".join(descriptive_lines)
        if isinstance(prompt_data, dict):
            system_prompt = prompt_data.get("system", "You are a helpful assistant.")
            user_prompt = prompt_data.get("format", "{lines}").format(lines=lines_text)
        else:
            # If ever a style is mapped directly to string
            system_prompt = "You are a helpful assistant."
            user_prompt = str(prompt_data)
        return system_prompt, user_prompt

    def _call_gpt(self, system_prompt: str, user_prompt: str) -> Tuple[str, int]:
        """
        Call Azure OpenAI with a short retry loop on RateLimitError.
        """
        retries = 3
        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return resp.choices[0].message.content, attempt
            except RateLimitError as e:
                print(f"⚠️ Rate limit (attempt {attempt}/{retries}), waiting 60s...")
                last_err = e
                time.sleep(60)
            except APIError as e:
                last_err = e
                break
            except Exception as e:
                last_err = e
                break
        if last_err:
            raise RuntimeError(f"❌ Summarization failed: {last_err}") from last_err
        raise RuntimeError("❌ Summarization failed for an unknown reason.")

    def _build_descriptive_lines(self, annotated_sentences: List[Dict[str, Any]], preset_key: PromptStyle) -> List[str]:
        """
        Create the descriptive lines injected into the prompt, adapted per style.
        """
        lines: List[str] = []
        for entry in annotated_sentences:
            emotion_list = entry.get("emotions", [])
            if not isinstance(emotion_list, list) or not emotion_list:
                continue

            strong = [e for e in emotion_list if isinstance(e, dict) and float(e.get("score", 0.0)) >= self.emotion_threshold]
            if not strong:
                continue

            top = max(strong, key=lambda e: float(e.get("score", 0.0)))
            speaker = entry.get("speaker", "?")
            text = entry.get("text", "")

            if preset_key in {PromptStyle.EMOTIONAL_STORY, PromptStyle.ALL_IN_ONE}:
                lines.append(f'**Speaker {speaker} ({str(top.get("label","")).lower()})**: "{text}"')
            elif preset_key == PromptStyle.PER_SPEAKER:
                lines.append(f'Speaker {speaker}: "{text}"  \\ Emotion: **{top.get("label","")}**')
            elif preset_key == PromptStyle.ANALYTICAL:
                pct = round(float(top.get("score", 0.0)) * 100)
                lines.append(f'- Speaker {speaker} | Emotion: {top.get("label","")} ({pct}%) | "{text}"')
            else:
                pct = round(float(top.get("score", 0.0)) * 100, 2)
                lines.append(f'{speaker} said: "{text}" — emotion detected: **{str(top.get("label","")).lower()}** ({pct}%)')
        return lines

    def annotate_by_matching(
        self,
        transcript: List[Dict[str, Any]],
        emotions: List[Dict[str, Any]],
        time_threshold: float = 0.05,
        similarity_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        """
        Match transcript items to emotion analyses using temporal proximity + textual similarity.
        """
        annotated: List[Dict[str, Any]] = []

        for t in transcript:
            t_text = str(t.get("text", "")).strip()
            t_start = float(t.get("start_time", 0.0))

            match = None
            for e in emotions:
                e_text = str(e.get("text", "")).strip()
                e_start = float(e.get("start_time", 0.0))

                time_match = abs(t_start - e_start) <= float(time_threshold)
                text_match = SequenceMatcher(None, t_text, e_text).ratio() >= float(similarity_threshold)

                if time_match and text_match:
                    match = e
                    break

            annotated.append({
                "speaker": t.get("speaker", "?"),
                "text": t_text,
                "start_time": t.get("start_time"),
                "end_time": t.get("end_time"),
                "emotions": match.get("emotions", []) if match else []
            })

        return annotated

    # ---------------- Parsing helpers (gentle, fault-tolerant) ----------------

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Try to extract a JSON object from the model's output (supports fenced blocks).
        Returns None if not found or invalid.
        """
        # ```json ... ``` or { ... }
        code_blocks = re.findall(r"```json\\s*(\\{.*?\\})\\s*```", text, flags=re.DOTALL)
        candidates = code_blocks + re.findall(r"(\\{.*\\})", text, flags=re.DOTALL)
        for blob in candidates:
            try:
                return json.loads(blob)
            except Exception:
                continue
        return None

    def _extract_action_items_from_html(self, text: str) -> List[Dict[str, str]]:
        """
        Parse the required HTML table (ID, Task, Owner, Due Date) if present.
        Ignores header row. Strips inner tags.
        """
        rows: List[Dict[str, str]] = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.DOTALL | re.IGNORECASE):
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.DOTALL | re.IGNORECASE)
            norm = [re.sub(r"<.*?>", "", c, flags=re.DOTALL).strip() for c in cells]
            if len(norm) == 4 and not any(h in norm for h in ["ID", "Task", "Owner", "Due Date"]):
                rows.append({"ID": norm[0], "Task": norm[1], "Owner": norm[2], "Due Date": norm[3]})
        return rows

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Capture sections delineated by bold/emoji headers as used in our presets.
        Returns a mapping of header -> body.
        """
        parts = re.split(r"\\n(?=\\*\\*[^*\\n]+?\\*\\*)", text)
        sections: Dict[str, str] = {}
        for part in parts:
            m = re.match(r"\\*\\*([^*]+)\\*\\*\\s*\\n(.*)", part, flags=re.DOTALL)
            if m:
                header = m.group(1).strip()
                body = m.group(2).strip()
                sections[header] = body
        return sections

from __future__ import annotations

from typing import List, Dict
from openai.lib.azure import AzureOpenAI          # <- fixes "__all__" lint warning
from openai import RateLimitError, APIError, APITimeoutError
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, \
    ChatCompletionUserMessageParam

from app.core.config.providers.azure.openai import AzureOpenAIConfig
from app.interfaces.services.summary import Summarizer, SummaryInput, SummaryOutput
from app.services.summary.prompts.prompts import PROMPT_PRESETS


class AzureOpenAISummarizer(Summarizer):
    """
    Abstractive summarizer using Azure OpenAI (Chat Completions).
    Matches: def summarize(self, req: SummaryInput) -> SummaryOutput
    """

    def __init__(self, cfg: AzureOpenAIConfig):
        self._cfg = cfg
        self.client = AzureOpenAI(
            api_key=cfg.api_key,
            api_version=cfg.api_version,
            azure_endpoint=cfg.endpoint,
        )

    def summarize(self, req: SummaryInput) -> SummaryOutput:
        messages = self._build_messages(req)  # -> List[ChatCompletionMessageParam]
        max_tokens = int(req.max_tokens or self._cfg.max_output_tokens)

        try:
            resp = self.client.chat.completions.create(
                model=self._cfg.deployment,           # Azure "deployment name"
                messages=messages,
                temperature=self._cfg.temperature,
                max_tokens=max_tokens,
            )
            text = (resp.choices[0].message.content or "").strip()
            usage: Dict[str, float] = {
                "prompt_tokens": float(getattr(resp.usage, "prompt_tokens", 0) or 0),
                "completion_tokens": float(getattr(resp.usage, "completion_tokens", 0) or 0),
                "total_tokens": float(getattr(resp.usage, "total_tokens", 0) or 0),
            }
            return SummaryOutput(
                summary=text,
                per_speaker=None,
                bullets=None,
                usage=usage,
            )
        except (RateLimitError, APITimeoutError, APIError):
            # Keep contract: usage is Optional[Dict[str, float]] -> return None on error
            return SummaryOutput(
                summary="",
                per_speaker=None,
                bullets=None,
                usage=None,
            )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_messages(req: SummaryInput) -> List[ChatCompletionMessageParam]:
        # Resolve style preset (case-insensitive; fallback to ALL_IN_ONE)
        style_key = (req.style or "ALL_IN_ONE")
        preset = (
            PROMPT_PRESETS.get(style_key)
            or PROMPT_PRESETS.get(style_key.lower())
            or PROMPT_PRESETS.get(style_key.upper())
            or PROMPT_PRESETS.get("ALL_IN_ONE")
            or ""
        )

        # Build lines: "Speaker: text [top_emotion]"
        lines: List[str] = []
        for s in req.segments:
            spk = str(s.speaker) if s.speaker is not None else "SPEAKER"
            txt = (s.text or "").strip()

            emo_hint = ""
            if s.emotions and getattr(s.emotions, "emotion_analysis", None):
                lab, _ = max(s.emotions.emotions_intensity_dict.items(), key=lambda kv: kv[1])
                emo_hint = f" [{lab}]"

            lines.append(f"{spk}: {txt}{emo_hint}")

        convo = "\n".join(lines)

        # Optional language / metadata
        extra_parts: List[str] = []
        if req.language:
            extra_parts.append(f"Please answer in: {req.language}")
        if req.metadata:
            meta_str = "; ".join(f"{k}={v}" for k, v in req.metadata.items())
            extra_parts.append(f"Context: {meta_str}")
        extra = ("\n\n" + "\n".join(extra_parts)) if extra_parts else ""

        # Return messages typed as ChatCompletionMessageParam list
        system_msg: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": preset,
        }
        user_msg: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": f"Conversation:\n{convo}{extra}",
        }
        return [system_msg, user_msg]

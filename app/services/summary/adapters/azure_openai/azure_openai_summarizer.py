from __future__ import annotations
from openai import AzureOpenAI, RateLimitError, APIError, APITimeoutError
from app.ports.services.summary.summarizer import Summarizer, SummaryInput, SummaryOutput
from app.services.summary.prompts.prompts import PROMPT_PRESETS
from app.core.config import AzureOpenAIConfig


class AzureOpenAISummarizer(Summarizer):
    """
    Abstractive summarizer using Azure OpenAI (chat.completions).
    Expects req.style to be a key in PROMPT_PRESETS.
    """
    def __init__(self, cfg: AzureOpenAIConfig):
        self.cfg = cfg
        self.client = AzureOpenAI(
            api_key=cfg.api_key,
            api_version=cfg.api_version,
            azure_endpoint=cfg.endpoint,
            azure_deployment=cfg.deployment,
        )

    @staticmethod
    def _build_messages(req: SummaryInput) -> list:
        style_key = (req.get("style") or "ALL_IN_ONE").lower()
        system_prompt = PROMPT_PRESETS.get(style_key) or PROMPT_PRESETS.get("all_in_one") or ""
        # Join conversation text with optional speaker tags and minimal emotion hints
        lines = []
        for s in req.get("segments", []):
            spk = str(s.get("speaker", "SPEAKER"))
            txt = (s.get("text") or "").strip()
            emo = s.get("emotions")
            emo_hint = ""
            if isinstance(emo, dict) and len(emo) > 0:
                # pick top-1 as a soft hint
                lab = max(emo.items(), key=lambda kv: kv[1])[0]
                emo_hint = f" [{lab}]"
            elif isinstance(emo, list) and emo:
                emo_hint = f" [{emo[0]}]"
            lines.append(f"{spk}: {txt}{emo_hint}")
        convo = "\n".join(lines)

        user_extra = []
        if req.get("language"):
            user_extra.append(f"Please answer in: {req['language']}")
        if req.get("metadata"):
            user_extra.append("Context: " + "; ".join(f"{k}={v}" for k, v in req["metadata"].items()))
        extra = ("\n\n" + "\n".join(user_extra)) if user_extra else ""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Conversation:\n{convo}{extra}"}
        ]

    def summarize(self, req: SummaryInput) -> SummaryOutput:
        msgs = self._build_messages(req)
        max_tokens = int(req.get("max_tokens") or self.cfg.max_output_tokens)
        try:
            resp = self.client.chat.completions.create(
                model=self.cfg.deployment,
                messages=msgs,
                temperature=self.cfg.temperature,
                max_tokens=max_tokens,
            )
            text = (resp.choices[0].message.content or "").strip()
            usage = {"prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                     "completion_tokens": getattr(resp.usage, "completion_tokens", 0)}
            return {"summary": text, "usage": usage}
        except (RateLimitError, APITimeoutError, APIError) as e:
            # Graceful error; upstream can retry/backoff
            return {"summary": "", "usage": {"error": str(e)}}


from __future__ import annotations
from app.core.config.services import SummarizationConfig
from app.services.summary.registry import build_summarizer, list_summarizers
from app.state.app_states import SummarizationState

def wire_summarization(
    summarization_cfg: SummarizationConfig,
) -> SummarizationState:
    summarization = SummarizationState()
    name = (getattr(summarization_cfg, "main_summarizer", "") or "").strip().lower()
    if not name:
        raise ValueError("SummarizationConfig.main_summarizer is empty")

    try:
        summarization.summarizer = build_summarizer(name, summarization_cfg)
    except KeyError:
        raise ValueError(
            f"No summarizer plugin registered for: '{name}'. "
            f"Available: {', '.join(list_summarizers())}"
        )
    return summarization

from app.services.summary.plugins import SUMMARIZER_PLUGINS
from app.core.config import SummarizationConfig
from app.state.app_states import SummarizationState


def wire_summarization(summarization: SummarizationState, summarization_cfg: SummarizationConfig) -> None:
    if summarization is None:
        summarization = SummarizationState()
    builder = SUMMARIZER_PLUGINS.get(summarization_cfg.main_summarizer)
    if not builder:
        raise ValueError(f"No transcriber plugin registered for backend: {summarization_cfg.main_summarizer}")
    summarization.summarizer = builder(summarization_cfg)
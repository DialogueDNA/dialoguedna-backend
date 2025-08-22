from app.core.config.services import SummarizationConfig
from app.interfaces.services.summary import Summarizer
from app.services.summary.providers.azure.openai import AzureOpenAISummarizer
from app.services.summary.registry import register_summarizer


@register_summarizer("azure_openai")
def build_azure_openai_summarizer(summarization_cfg: SummarizationConfig) -> Summarizer:
    return AzureOpenAISummarizer(summarization_cfg.azure_openai)

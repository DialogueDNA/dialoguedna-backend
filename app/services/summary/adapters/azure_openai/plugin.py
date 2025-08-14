from app.core.config.services import SummarizationConfig
from app.ports.services.summary import Summarizer
from app.services.summary.adapters.azure_openai.azure_openai_summarizer import AzureOpenAISummarizer
from app.services.summary.plugins import register_summarizer


@register_summarizer("azure-openai")
def build_azure_openai_summarizer(summarization_cfg: SummarizationConfig) -> Summarizer:
    return AzureOpenAISummarizer(summarization_cfg.azure_openai)

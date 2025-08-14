from dataclasses import dataclass

from app.core.config.providers.azure_openai import AzureOpenAIConfig
import app.core.environment as env

@dataclass(frozen=True)
class SummarizationConfig:
    """
    Unified field names used end-to-end.
    Any backend builder picks only the args it needs via inspect.signature.
    """
    main_summarizer: str = env.SUMMARIZER_ADAPTER
    azure_openai: AzureOpenAIConfig = AzureOpenAIConfig()
from dataclasses import dataclass
import app.core.environment as env

@dataclass(frozen=True)
class AzureOpenAIConfig:
    # Azure OpenAI Configuration for Summarization
    endpoint: str = env.AZURE_OPENAI_ENDPOINT
    api_key: str = env.AZURE_OPENAI_API_KEY
    deployment: str = env.AZURE_OPENAI_DEPLOYMENT
    api_version: str = env.AZURE_OPENAI_API_VERSION
    temperature: float = env.AZURE_OPENAI_TEMPERATURE
    max_output_tokens: int = env.AZURE_OPENAI_MAX_OUTPUT_TOKENS
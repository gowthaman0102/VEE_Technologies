from functools import lru_cache

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.ollama_provider import OllamaLLMProvider


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    provider_name = settings.llm_provider.strip().lower()

    if provider_name == "ollama":
        return OllamaLLMProvider(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            timeout=settings.llm_timeout_seconds,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )

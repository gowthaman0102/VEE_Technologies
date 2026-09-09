from functools import lru_cache

from app.core.config import settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    provider_name = settings.embedding_provider.strip().lower()

    if provider_name == "sentence-transformers":
        return SentenceTransformerEmbeddingProvider(
            model_name=settings.embedding_model,
        )

    if provider_name == "openai":
        return OpenAIEmbeddingProvider(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        )

    raise ValueError(
        f"Unsupported embedding provider: {settings.embedding_provider}"
    )

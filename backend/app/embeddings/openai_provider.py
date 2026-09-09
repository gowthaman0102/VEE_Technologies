from openai import AsyncOpenAI

from app.core.config import settings
from app.embeddings.base import EmbeddingProvider, EmbeddingResult


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.model = model or settings.embedding_model
        self.dimensions = (
            settings.embedding_dimensions
            if dimensions is None
            else dimensions
        )

        if self.dimensions <= 0:
            raise ValueError("Embedding dimensions must be greater than zero.")

        if client is not None:
            self.client = client
            return

        resolved_api_key = api_key or settings.openai_api_key

        if not resolved_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required to use the OpenAI embedding provider."
            )

        self.client = AsyncOpenAI(api_key=resolved_api_key)

    async def embed_text(self, text: str) -> EmbeddingResult:
        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError("Embedding input cannot be empty.")

        response = await self.client.embeddings.create(
            model=self.model,
            input=normalized_text,
            dimensions=self.dimensions,
            encoding_format="float",
        )

        if not response.data:
            raise RuntimeError(
                "Embedding provider returned no embedding data."
            )

        vector = list(response.data[0].embedding)

        if len(vector) != self.dimensions:
            raise RuntimeError(
                "Embedding provider returned an unexpected vector dimension: "
                f"expected {self.dimensions}, received {len(vector)}."
            )

        return EmbeddingResult(
            vector=vector,
            model=self.model,
            dimensions=len(vector),
        )

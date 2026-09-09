import asyncio

from sentence_transformers import SentenceTransformer

from app.embeddings.base import EmbeddingProvider, EmbeddingResult


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Local, free embedding provider using sentence-transformers."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        dimensions = self.model.get_embedding_dimension()

        if dimensions is None or dimensions <= 0:
            raise ValueError(
                "Unable to determine sentence-transformer embedding dimensions."
            )

        self.dimensions = dimensions

    async def embed_text(self, text: str) -> EmbeddingResult:
        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError("Text cannot be empty.")

        vector = await asyncio.to_thread(
            self.model.encode,
            normalized_text,
            normalize_embeddings=True,
        )

        vector_list = [
            float(value)
            for value in vector.tolist()
        ]

        if len(vector_list) != self.dimensions:
            raise ValueError(
                "Embedding dimensions do not match the loaded model."
            )

        return EmbeddingResult(
            vector=vector_list,
            model=self.model_name,
            dimensions=self.dimensions,
        )

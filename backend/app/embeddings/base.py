from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    model: str
    dimensions: int


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate an embedding for a single text input."""
        raise NotImplementedError

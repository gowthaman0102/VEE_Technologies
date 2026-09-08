from abc import ABC, abstractmethod

from app.ingestion.types import CollectedArticle


class BaseCollector(ABC):
    @abstractmethod
    async def collect(self) -> list[CollectedArticle]:
        """Collect articles from a news source."""
        raise NotImplementedError

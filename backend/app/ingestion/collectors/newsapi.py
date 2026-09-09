from datetime import datetime

import httpx

from app.ingestion.collectors.base import BaseCollector
from app.ingestion.types import CollectedArticle


class NewsAPICollector(BaseCollector):
    """Collect news articles using the NewsAPI Everything endpoint."""

    def __init__(
        self,
        api_key: str,
        query: str,
        base_url: str = "https://newsapi.org/v2",
        language: str = "en",
        page_size: int = 100,
        timeout: float = 15.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("NewsAPI API key is required")

        if not query.strip():
            raise ValueError("NewsAPI query is required")

        self.api_key = api_key
        self.query = query
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.page_size = min(max(page_size, 1), 100)
        self.timeout = timeout

    async def collect(self) -> list[CollectedArticle]:
        params = {
            "q": self.query,
            "language": self.language,
            "sortBy": "publishedAt",
            "pageSize": self.page_size,
            "apiKey": self.api_key,
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/everything",
                params=params,
            )

            response.raise_for_status()
            payload = response.json()

        if payload.get("status") != "ok":
            message = payload.get(
                "message",
                "NewsAPI returned an unsuccessful response",
            )
            raise RuntimeError(message)

        articles: list[CollectedArticle] = []

        for item in payload.get("articles", []):
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()

            if not title or not url:
                continue

            source = item.get("source") or {}
            source_name = (
                source.get("name")
                or "NewsAPI"
            )

            articles.append(
                CollectedArticle(
                    source_name=source_name,
                    source_type="newsapi",
                    external_id=url,
                    title=title,
                    url=url,
                    author=item.get("author"),
                    description=item.get("description"),
                    raw_content=item.get("content"),
                    language=self.language,
                    published_at=self._parse_datetime(
                        item.get("publishedAt")
                    ),
                )
            )

        return articles

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None

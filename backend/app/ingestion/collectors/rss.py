from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.ingestion.collectors.base import BaseCollector
from app.ingestion.types import CollectedArticle


class RSSCollector(BaseCollector):
    def __init__(
        self,
        feed_url: str,
        source_name: str,
        language: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        if not feed_url.strip():
            raise ValueError("RSS feed URL is required")

        if not source_name.strip():
            raise ValueError("RSS source name is required")

        if timeout <= 0:
            raise ValueError(
                "RSS timeout must be greater than zero"
            )

        self.feed_url = feed_url
        self.source_name = source_name
        self.language = language
        self.timeout = timeout

    async def collect(self) -> list[CollectedArticle]:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                self.feed_url,
            )

            response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

        articles: list[CollectedArticle] = []

        for entry in feed.entries:
            title = entry.get(
                "title",
                "",
            ).strip()

            url = entry.get(
                "link",
                "",
            ).strip()

            if not title or not url:
                continue

            entry_source = entry.get("source") or {}
            publisher = (
                entry_source.get("title")
                if isinstance(entry_source, dict)
                else None
            )
            source_name = (
                publisher.strip()
                if self.source_name.lower().startswith("google news")
                and isinstance(publisher, str)
                and publisher.strip()
                else self.source_name
            )

            articles.append(
                CollectedArticle(
                    source_name=source_name,
                    source_type="rss",
                    external_id=(
                        entry.get("id")
                        or url
                    ),
                    title=title,
                    url=url,
                    author=entry.get("author"),
                    description=entry.get(
                        "summary"
                    ),
                    raw_content=None,
                    language=self.language,
                    published_at=(
                        self._parse_published_at(
                            entry
                        )
                    ),
                )
            )

        return articles

    @staticmethod
    def _parse_published_at(
        entry,
    ) -> datetime | None:
        published = (
            entry.get("published")
            or entry.get("updated")
        )

        if not published:
            return None

        try:
            value = parsedate_to_datetime(
                published
            )

            if value.tzinfo is None:
                value = value.replace(
                    tzinfo=timezone.utc
                )

            return value

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None

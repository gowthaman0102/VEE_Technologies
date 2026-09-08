import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from app.ingestion.collectors.base import BaseCollector
from app.ingestion.types import CollectedArticle


class RSSCollector(BaseCollector):
    def __init__(
        self,
        feed_url: str,
        source_name: str,
        language: str | None = None,
    ) -> None:
        self.feed_url = feed_url
        self.source_name = source_name
        self.language = language

    async def collect(self) -> list[CollectedArticle]:
        feed = await asyncio.to_thread(
            feedparser.parse,
            self.feed_url,
        )

        articles: list[CollectedArticle] = []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()

            if not title or not url:
                continue

            articles.append(
                CollectedArticle(
                    source_name=self.source_name,
                    source_type="rss",
                    external_id=entry.get("id") or url,
                    title=title,
                    url=url,
                    author=entry.get("author"),
                    description=entry.get("summary"),
                    raw_content=None,
                    language=self.language,
                    published_at=self._parse_published_at(
                        entry
                    ),
                )
            )

        return articles

    @staticmethod
    def _parse_published_at(entry) -> datetime | None:
        published = (
            entry.get("published")
            or entry.get("updated")
        )

        if not published:
            return None

        try:
            value = parsedate_to_datetime(published)

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

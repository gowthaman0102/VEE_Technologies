from dataclasses import dataclass
from typing import Literal


SourceType = Literal["rss", "newsapi"]


@dataclass(frozen=True)
class NewsSource:
    key: str
    name: str
    source_type: SourceType
    url: str | None = None
    query: str | None = None
    language: str = "en"
    enabled: bool = True
    category: str | None = None


NEWS_SOURCES: tuple[NewsSource, ...] = (
    NewsSource(
        key="google_news_vee",
        name="Google News - VEE Technologies",
        source_type="rss",
        url=(
            "https://news.google.com/rss/search"
            "?q=%22VEE+Technologies%22"
            "&hl=en-IN"
            "&gl=IN"
            "&ceid=IN:en"
        ),
        language="en",
        category="company",
    ),
    NewsSource(
        key="newsapi_vee",
        name="NewsAPI - VEE Technologies",
        source_type="newsapi",
        query="VEE Technologies",
        language="en",
        category="company",
    ),
)


def get_enabled_sources() -> list[NewsSource]:
    return [
        source
        for source in NEWS_SOURCES
        if source.enabled
    ]


def get_source(
    key: str,
) -> NewsSource | None:
    return next(
        (
            source
            for source in NEWS_SOURCES
            if source.key == key
        ),
        None,
    )


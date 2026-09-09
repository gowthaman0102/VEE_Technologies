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
        key="google_news_payu",
        name="Google News - PayU India",
        source_type="rss",
        url=(
            "https://news.google.com/rss/search"
            "?q=PayU+India"
            "&hl=en-IN"
            "&gl=IN"
            "&ceid=IN:en"
        ),
        language="en",
        category="company",
    ),
    NewsSource(
        key="newsapi_payu",
        name="NewsAPI - PayU India",
        source_type="newsapi",
        query='"PayU" AND India',
        language="en",
        category="company",
    ),
    NewsSource(
        key="et_government_digital_payments",
        name="ET Government - Digital Payments",
        source_type="rss",
        url=(
            "https://government.economictimes.indiatimes.com/"
            "rss/digital-payments"
        ),
        language="en",
        category="payments",
    ),
    NewsSource(
        key="et_government_policy",
        name="ET Government - Policy",
        source_type="rss",
        url=(
            "https://government.economictimes.indiatimes.com/"
            "rss/policy"
        ),
        language="en",
        category="regulatory",
    ),
    NewsSource(
        key="rbi_press_releases",
        name="RBI - Press Releases",
        source_type="rss",
        url="https://rbi.org.in/pressreleases_rss.xml",
        language="en",
        category="regulatory",
    ),
    NewsSource(
        key="rbi_notifications",
        name="RBI - Notifications",
        source_type="rss",
        url="https://rbi.org.in/notifications_rss.xml",
        language="en",
        category="regulatory",
    ),
)


def get_enabled_sources() -> list[NewsSource]:
    return [
        source
        for source in NEWS_SOURCES
        if source.enabled
    ]


def get_source(key: str) -> NewsSource | None:
    return next(
        (
            source
            for source in NEWS_SOURCES
            if source.key == key
        ),
        None,
    )

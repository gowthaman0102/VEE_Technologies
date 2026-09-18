from dataclasses import dataclass
from typing import Literal


SourceType = Literal["rss", "newsapi", "html_listing"]


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
        key="openai_official_news",
        name="OpenAI Official News",
        source_type="rss",
        url="https://openai.com/news/rss.xml",
        language="en",
        category="company",
    ),
    NewsSource(
        key="google_news_openai",
        name="Google News - OpenAI",
        source_type="rss",
        url=(
            "https://news.google.com/rss/search"
            "?q=%22OpenAI%22&hl=en-US&gl=US&ceid=US:en"
        ),
        language="en",
        category="company",
    ),
    NewsSource(
        key="google_news_openai_chatgpt",
        name="Google News - OpenAI ChatGPT",
        source_type="rss",
        url=(
            "https://news.google.com/rss/search"
            "?q=%22OpenAI%22+ChatGPT&hl=en-US&gl=US&ceid=US:en"
        ),
        language="en",
        category="company",
    ),
    NewsSource(
        key="google_news_openai_research_safety",
        name="Google News - OpenAI Research and Safety",
        source_type="rss",
        url=(
            "https://news.google.com/rss/search"
            "?q=%22OpenAI%22+(research+OR+safety+OR+security)"
            "&hl=en-US&gl=US&ceid=US:en"
        ),
        language="en",
        category="company",
    ),
    NewsSource(
        key="google_news_openai_business",
        name="Google News - OpenAI Business and Partnerships",
        source_type="rss",
        url=(
            "https://news.google.com/rss/search"
            "?q=%22OpenAI%22+(partnership+OR+Microsoft+OR+enterprise+OR+acquisition)"
            "&hl=en-US&gl=US&ceid=US:en"
        ),
        language="en",
        category="company",
    ),
    NewsSource(
        key="newsapi_openai",
        name="NewsAPI - OpenAI",
        source_type="newsapi",
        query='"OpenAI"',
        language="en",
        category="company",
    ),
    NewsSource(
        key="newsapi_openai_chatgpt",
        name="NewsAPI - OpenAI ChatGPT",
        source_type="newsapi",
        query='"OpenAI" AND ChatGPT',
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


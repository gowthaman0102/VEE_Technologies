from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote_plus

from app.schemas.client_configuration import ClientConfiguration


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


def get_sources_for_config(
    config: ClientConfiguration,
) -> list[NewsSource]:
    """Build shared source adapters from client data, never client code."""
    sources: list[NewsSource] = []
    source_config = config.sources
    query_terms = [f'"{alias}"' for alias in config.aliases if alias.strip()]
    topic_terms = [topic.strip() for topic in config.monitoring_topics if topic.strip()]
    query = " OR ".join(query_terms)
    if topic_terms:
        query = f"({query}) AND ({' OR '.join(topic_terms)})"

    if source_config.google_news_enabled and query:
        encoded_query = quote_plus(query)
        sources.append(
            NewsSource(
                key="google_news_company",
                name=f"Google News - {config.company_name}",
                source_type="rss",
                url=(
                    "https://news.google.com/rss/search"
                    f"?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
                ),
                category="company",
            )
        )

    if source_config.newsapi_enabled and query:
        sources.append(
            NewsSource(
                key="newsapi_company",
                name=f"NewsAPI - {config.company_name}",
                source_type="newsapi",
                query=query,
                category="company",
            )
        )

    for index, source_url in enumerate(source_config.official_sources):
        sources.append(
            NewsSource(
                key=f"official_company_{index}",
                name=f"{config.company_name} Official Source {index + 1}",
                source_type="rss",
                url=source_url,
                category="official",
            )
        )

    excluded = {item.lower() for item in source_config.excluded_sources}
    return [
        source
        for source in sources
        if source.name.lower() not in excluded
        and source.key.lower() not in excluded
    ]


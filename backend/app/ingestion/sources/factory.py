from app.ingestion.collectors import (
    BaseCollector,
    HTMLListingCollector,
    NewsAPICollector,
    RSSCollector,
)
from app.ingestion.sources.registry import NewsSource


def build_collector(
    source: NewsSource,
    *,
    newsapi_api_key: str | None = None,
    newsapi_base_url: str = "https://newsapi.org/v2",
) -> BaseCollector:
    if source.source_type == "html_listing":
        if not source.url:
            raise ValueError(
                f"HTML listing source '{source.key}' requires a URL"
            )

        return HTMLListingCollector(
            listing_url=source.url,
            source_name=source.name,
            language=source.language,
        )

    if source.source_type == "rss":
        if not source.url:
            raise ValueError(
                f"RSS source '{source.key}' requires a URL"
            )

        return RSSCollector(
            feed_url=source.url,
            source_name=source.name,
            language=source.language,
        )

    if source.source_type == "newsapi":
        if not source.query:
            raise ValueError(
                f"NewsAPI source '{source.key}' requires a query"
            )

        if not newsapi_api_key:
            raise ValueError(
                "NewsAPI API key is required"
            )

        return NewsAPICollector(
            api_key=newsapi_api_key,
            query=source.query,
            base_url=newsapi_base_url,
            language=source.language,
        )

    raise ValueError(
        f"Unsupported source type: {source.source_type}"
    )

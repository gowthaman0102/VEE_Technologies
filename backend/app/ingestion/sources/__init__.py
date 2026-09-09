from app.ingestion.sources.factory import build_collector
from app.ingestion.sources.registry import (
    NEWS_SOURCES,
    NewsSource,
    get_enabled_sources,
    get_source,
)

__all__ = [
    "NEWS_SOURCES",
    "NewsSource",
    "build_collector",
    "get_enabled_sources",
    "get_source",
]

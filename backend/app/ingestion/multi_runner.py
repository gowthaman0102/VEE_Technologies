from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.runner import IngestionResult, run_collector
from app.ingestion.sources import (
    NewsSource,
    build_collector,
)


@dataclass
class SourceIngestionResult:
    source_key: str
    source_name: str
    collected: int
    inserted: int
    skipped: int
    error: str | None = None


async def run_sources(
    db: AsyncSession,
    sources: list[NewsSource],
    *,
    newsapi_api_key: str | None = None,
    newsapi_base_url: str = "https://newsapi.org/v2",
    per_source_limit: int | None = None,
) -> list[SourceIngestionResult]:
    results: list[SourceIngestionResult] = []

    for source in sources:
        try:
            collector = build_collector(
                source,
                newsapi_api_key=newsapi_api_key,
                newsapi_base_url=newsapi_base_url,
            )

            result: IngestionResult = await run_collector(
                db=db,
                collector=collector,
                limit=per_source_limit,
            )

            results.append(
                SourceIngestionResult(
                    source_key=source.key,
                    source_name=source.name,
                    collected=result.collected,
                    inserted=result.inserted,
                    skipped=result.skipped,
                )
            )

        except Exception as exc:
            results.append(
                SourceIngestionResult(
                    source_key=source.key,
                    source_name=source.name,
                    collected=0,
                    inserted=0,
                    skipped=0,
                    error=str(exc),
                )
            )

    return results

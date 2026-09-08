from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.collectors.base import BaseCollector
from app.services.article_service import save_collected_article


@dataclass
class IngestionResult:
    collected: int
    inserted: int
    skipped: int


async def run_collector(
    db: AsyncSession,
    collector: BaseCollector,
    limit: int | None = None,
) -> IngestionResult:
    articles = await collector.collect()

    if limit is not None:
        articles = articles[:limit]

    inserted = 0
    skipped = 0

    for article in articles:
        _, created = await save_collected_article(
            db,
            article,
        )

        if created:
            inserted += 1
        else:
            skipped += 1

    return IngestionResult(
        collected=len(articles),
        inserted=inserted,
        skipped=skipped,
    )

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.processing.extractor import ArticleExtractor
from app.services.article_processing_service import (
    ArticleProcessingResult,
    process_article,
)


@dataclass
class BatchProcessingResult:
    selected: int
    success: int
    skipped: int
    failed: int
    results: list[ArticleProcessingResult]


async def get_processable_articles(
    db: AsyncSession,
    *,
    limit: int = 20,
    include_failed: bool = False,
) -> list[Article]:
    statuses = ["pending"]

    if include_failed:
        statuses.append("failed")

    result = await db.execute(
        select(Article)
        .where(
            Article.extraction_status.in_(
                statuses
            )
        )
        .order_by(
            Article.collected_at.asc(),
            Article.id.asc(),
        )
        .limit(limit)
    )

    return list(
        result.scalars().all()
    )


async def process_articles_batch(
    db: AsyncSession,
    *,
    limit: int = 20,
    include_failed: bool = False,
    extractor: ArticleExtractor | None = None,
) -> BatchProcessingResult:
    if limit < 1:
        raise ValueError(
            "Batch processing limit must be at least 1"
        )

    articles = await get_processable_articles(
        db,
        limit=limit,
        include_failed=include_failed,
    )

    results: list[
        ArticleProcessingResult
    ] = []

    success = 0
    skipped = 0
    failed = 0

    for article in articles:
        try:
            result = await process_article(
                db,
                article,
                extractor=extractor,
            )

        except Exception as exc:
            await db.rollback()

            result = ArticleProcessingResult(
                article_id=article.id,
                status="failed",
                error=(
                    "Processing pipeline error: "
                    f"{type(exc).__name__}"
                ),
            )

        results.append(result)

        if result.status == "success":
            success += 1
        elif result.status == "skipped":
            skipped += 1
        else:
            failed += 1

    return BatchProcessingResult(
        selected=len(articles),
        success=success,
        skipped=skipped,
        failed=failed,
        results=results,
    )

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.models.article import Article
from app.services.article_embedding_service import (
    ArticleEmbeddingResult,
    embed_article,
)


@dataclass
class BatchEmbeddingResult:
    selected: int
    success: int
    skipped: int
    failed: int
    results: list[ArticleEmbeddingResult]


async def get_embeddable_articles(
    db: AsyncSession,
    *,
    limit: int = 20,
    include_failed: bool = False,
) -> list[Article]:
    if limit < 1:
        raise ValueError("Batch limit must be at least 1.")

    statuses = ["pending"]

    if include_failed:
        statuses.append("failed")

    statement = (
        select(Article)
        .where(
            Article.extraction_status == "success",
            Article.cleaned_content.is_not(None),
            func.length(
                func.trim(Article.cleaned_content)
            ) > 0,
            Article.embedding_status.in_(statuses),
        )
        .order_by(
            Article.collected_at.asc(),
            Article.id.asc(),
        )
        .limit(limit)
    )

    result = await db.execute(statement)

    return list(
        result.scalars().all()
    )


async def process_embedding_batch(
    db: AsyncSession,
    *,
    limit: int = 20,
    include_failed: bool = False,
    provider: EmbeddingProvider | None = None,
) -> BatchEmbeddingResult:
    if limit < 1:
        raise ValueError("Batch limit must be at least 1.")

    articles = await get_embeddable_articles(
        db,
        limit=limit,
        include_failed=include_failed,
    )

    if not articles:
        return BatchEmbeddingResult(
            selected=0,
            success=0,
            skipped=0,
            failed=0,
            results=[],
        )

    embedding_provider = (
        provider
        if provider is not None
        else get_embedding_provider()
    )

    results: list[ArticleEmbeddingResult] = []

    success = 0
    skipped = 0
    failed = 0

    for article in articles:
        article_id = article.id

        try:
            result = await embed_article(
                db,
                article,
                provider=embedding_provider,
            )

        except Exception as exc:
            await db.rollback()

            error = (
                "Embedding pipeline error: "
                f"{type(exc).__name__}"
            )

            await db.execute(
                update(Article)
                .where(
                    Article.id == article_id
                )
                .values(
                    embedding=None,
                    embedding_model=None,
                    embedding_status="failed",
                    embedding_error=error,
                    embedded_at=datetime.now(timezone.utc),
                )
            )

            await db.commit()

            result = ArticleEmbeddingResult(
                article_id=article_id,
                status="failed",
                error=error,
            )

        results.append(result)

        if result.status == "success":
            success += 1
        elif result.status == "skipped":
            skipped += 1
        else:
            failed += 1

    return BatchEmbeddingResult(
        selected=len(articles),
        success=success,
        skipped=skipped,
        failed=failed,
        results=results,
    )

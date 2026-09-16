from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_sentiment import (
    ArticleSentiment,
)
from app.schemas.article_sentiment import (
    ArticleSentimentResult,
)


async def get_article_sentiment(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
) -> ArticleSentiment | None:
    result = await db.execute(
        select(ArticleSentiment).where(
            ArticleSentiment.article_id
            == article_id,
            ArticleSentiment.company_id
            == company_id,
        )
    )

    return result.scalar_one_or_none()


async def upsert_article_sentiment(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
    result: ArticleSentimentResult,
) -> ArticleSentiment:
    existing = await get_article_sentiment(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    if existing is None:
        existing = ArticleSentiment(
            article_id=article_id,
            company_id=company_id,
            label=result.label,
            score=result.score,
            reason=result.reason,
            model=result.model,
        )

        db.add(existing)

    else:
        existing.label = result.label
        existing.score = result.score
        existing.reason = result.reason
        existing.model = result.model

    await db.commit()
    await db.refresh(existing)

    return existing

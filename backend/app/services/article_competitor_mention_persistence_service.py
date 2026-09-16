from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_competitor_mention import (
    ArticleCompetitorMention,
)


async def get_article_competitor_mentions(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
) -> ArticleCompetitorMention | None:
    result = await db.execute(
        select(ArticleCompetitorMention).where(
            ArticleCompetitorMention.article_id
            == article_id,
            ArticleCompetitorMention.company_id
            == company_id,
        )
    )

    return result.scalar_one_or_none()


async def upsert_article_competitor_mentions(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
    competitors: list[str],
) -> ArticleCompetitorMention:
    existing = await get_article_competitor_mentions(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    normalized = list(
        dict.fromkeys(
            item.strip()
            for item in competitors
            if item and item.strip()
        )
    )

    if existing is None:
        existing = ArticleCompetitorMention(
            article_id=article_id,
            company_id=company_id,
            competitors=normalized,
        )

        db.add(existing)

    else:
        existing.competitors = normalized

    await db.commit()
    await db.refresh(existing)

    return existing

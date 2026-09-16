from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_business_impact import (
    ArticleBusinessImpact,
)
from app.schemas.article_business_impact import (
    ArticleBusinessImpactResult,
)


async def get_article_business_impact(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
) -> ArticleBusinessImpact | None:
    result = await db.execute(
        select(ArticleBusinessImpact).where(
            ArticleBusinessImpact.article_id
            == article_id,
            ArticleBusinessImpact.company_id
            == company_id,
        )
    )

    return result.scalar_one_or_none()


async def upsert_article_business_impact(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
    result: ArticleBusinessImpactResult,
) -> ArticleBusinessImpact:
    existing = await get_article_business_impact(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    if existing is None:
        existing = ArticleBusinessImpact(
            article_id=article_id,
            company_id=company_id,
            primary_category=(
                result.primary_category
            ),
            categories=result.categories,
            impact_summary=(
                result.impact_summary
            ),
            evidence=result.evidence,
            model=result.model,
        )

        db.add(existing)

    else:
        existing.primary_category = (
            result.primary_category
        )
        existing.categories = (
            result.categories
        )
        existing.impact_summary = (
            result.impact_summary
        )
        existing.evidence = (
            result.evidence
        )
        existing.model = result.model

    await db.commit()
    await db.refresh(existing)

    return existing

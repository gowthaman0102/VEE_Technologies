from sqlalchemy import select

from app.models.article_triage import ArticleTriage


async def get_article_triage(
    db,
    *,
    article_id: int,
    company_id: int,
) -> ArticleTriage | None:
    result = await db.execute(
        select(ArticleTriage).where(
            ArticleTriage.article_id == article_id,
            ArticleTriage.company_id == company_id,
        )
    )

    return result.scalar_one_or_none()

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_competitor_mention import ArticleCompetitorMention
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.event_cluster import EventClusterMembership
from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight
from app.services.active_company_profile_service import (
    get_active_company_profile,
)


@dataclass(frozen=True)
class ArticleRecoveryResult:
    requested: int
    queued_processing: int
    queued_intelligence: int
    already_complete: int


async def queue_incomplete_active_articles(
    db: AsyncSession,
    *,
    limit: int | None = None,
) -> ArticleRecoveryResult:
    profile = await get_active_company_profile(db)
    if profile is None:
        raise RuntimeError("No active company configured")

    query = select(Article).order_by(Article.id)
    if limit is not None:
        query = query.limit(limit)

    articles = list((await db.execute(query)).scalars().all())
    article_ids = [article.id for article in articles]
    if not article_ids:
        return ArticleRecoveryResult(0, 0, 0, 0)

    model_sets = {}
    for model in (
        ArticleSentiment,
        ArticleBusinessImpact,
        ArticleCompetitorMention,
        ArticleTriage,
        RiskAssessment,
        RiskInsight,
        EventClusterMembership,
    ):
        rows = await db.execute(
            select(model.article_id).where(
                model.company_id == profile.company_id,
                model.article_id.in_(article_ids),
            )
        )
        model_sets[model] = set(rows.scalars().all())

    queued_processing = 0
    queued_intelligence = 0
    already_complete = 0

    for article in articles:
        analysis_complete = all(
            article.id in model_sets[model]
            for model in model_sets
        )

        if article.extraction_status == "skipped":
            already_complete += 1
            continue

        if (
            article.extraction_status == "success"
            and article.embedding_status == "success"
            and analysis_complete
        ):
            already_complete += 1
            continue

        if (
            article.extraction_status == "success"
            and article.embedding_status == "success"
        ):
            celery_app.send_task(
                "intelligence.process_article",
                args=[article.id, profile.company_id],
            )
            queued_intelligence += 1
            continue

        celery_app.send_task(
            "processing.process_article",
            args=[article.id, profile.company_id],
        )
        queued_processing += 1

    return ArticleRecoveryResult(
        requested=len(articles),
        queued_processing=queued_processing,
        queued_intelligence=queued_intelligence,
        already_complete=already_complete,
    )

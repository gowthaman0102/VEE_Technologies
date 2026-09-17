from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.event_cluster import EventClusterMembership
from app.models.risk_assessment import RiskAssessment


@dataclass(frozen=True)
class SearchResultEnrichment:
    event_type: str | None = None
    sentiment: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None
    event_cluster_id: int | None = None


async def get_search_result_enrichments(
    db: AsyncSession,
    *,
    article_ids: list[int],
    company_id: int,
) -> dict[int, SearchResultEnrichment]:
    if not article_ids:
        return {}

    statement = (
        select(
            Article.id.label("article_id"),
            ArticleTriage.event_type.label(
                "event_type"
            ),
            ArticleSentiment.label.label(
                "sentiment"
            ),
            RiskAssessment.risk_level.label(
                "risk_level"
            ),
            RiskAssessment.risk_score.label(
                "risk_score"
            ),
            ArticleBusinessImpact.primary_category.label(
                "business_impact"
            ),
            EventClusterMembership.cluster_id.label(
                "event_cluster_id"
            ),
        )
        .join(
            ArticleTriage,
            (
                (ArticleTriage.article_id == Article.id)
                & (
                    ArticleTriage.company_id
                    == company_id
                )
            ),
        )
        .outerjoin(
            ArticleSentiment,
            (
                (ArticleSentiment.article_id == Article.id)
                & (
                    ArticleSentiment.company_id
                    == company_id
                )
            ),
        )
        .outerjoin(
            RiskAssessment,
            (
                (RiskAssessment.article_id == Article.id)
                & (
                    RiskAssessment.company_id
                    == company_id
                )
            ),
        )
        .outerjoin(
            ArticleBusinessImpact,
            (
                (
                    ArticleBusinessImpact.article_id
                    == Article.id
                )
                & (
                    ArticleBusinessImpact.company_id
                    == company_id
                )
            ),
        )
        .outerjoin(
            EventClusterMembership,
            (
                (
                    EventClusterMembership.article_id
                    == Article.id
                )
                & (
                    EventClusterMembership.company_id
                    == company_id
                )
            ),
        )
        .where(
            Article.id.in_(article_ids)
        )
    )

    rows = (await db.execute(statement)).all()

    return {
        row.article_id: SearchResultEnrichment(
            event_type=row.event_type,
            sentiment=row.sentiment,
            risk_level=row.risk_level,
            risk_score=(
                float(row.risk_score)
                if row.risk_score is not None
                else None
            ),
            business_impact=row.business_impact,
            event_cluster_id=row.event_cluster_id,
        )
        for row in rows
    }

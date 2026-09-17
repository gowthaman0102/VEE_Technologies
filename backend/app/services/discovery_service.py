from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.event_cluster import EventCluster, EventClusterMembership
from app.models.risk_assessment import RiskAssessment
from app.schemas.search_filters import SearchFilters
from app.services.search_enrichment_service import (
    get_search_result_enrichments,
)


@dataclass(frozen=True)
class KeywordSearchItem:
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None
    event_type: str | None = None
    sentiment: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None
    event_cluster_id: int | None = None


async def keyword_search(
    db: AsyncSession,
    *,
    query: str,
    company_id: int,
    limit: int = 50,
    filters: SearchFilters | None = None,
) -> list[KeywordSearchItem]:
    normalized = query.strip()

    if not normalized:
        raise ValueError("query must not be empty")

    pattern = f"%{normalized}%"
    filters = filters or SearchFilters()

    stmt = (
        select(Article)
        .join(
            ArticleTriage,
            ArticleTriage.article_id == Article.id,
        )
        .where(
            ArticleTriage.company_id == company_id,
            or_(
                Article.title.ilike(pattern),
                Article.description.ilike(pattern),
                Article.cleaned_content.ilike(pattern),
            ),
        )
    )

    if filters.start is not None:
        stmt = stmt.where(
            Article.published_at >= filters.start
        )

    if filters.end is not None:
        stmt = stmt.where(
            Article.published_at <= filters.end
        )

    if filters.source_name is not None:
        stmt = stmt.where(
            func.lower(Article.source_name)
            == filters.source_name.lower()
        )

    if filters.event_type is not None:
        stmt = stmt.where(
            func.lower(ArticleTriage.event_type)
            == filters.event_type.lower()
        )

    if filters.sentiment is not None:
        stmt = stmt.join(
            ArticleSentiment,
            (
                (ArticleSentiment.article_id == Article.id)
                & (
                    ArticleSentiment.company_id
                    == company_id
                )
            ),
        ).where(
            func.lower(ArticleSentiment.label)
            == filters.sentiment.lower()
        )

    if filters.risk_level is not None:
        stmt = stmt.join(
            RiskAssessment,
            (
                (RiskAssessment.article_id == Article.id)
                & (
                    RiskAssessment.company_id
                    == company_id
                )
            ),
        ).where(
            func.lower(RiskAssessment.risk_level)
            == filters.risk_level.lower()
        )

    if filters.business_impact is not None:
        stmt = stmt.join(
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
        ).where(
            func.lower(
                ArticleBusinessImpact.primary_category
            )
            == filters.business_impact.lower()
        )

    if filters.event_cluster_id is not None:
        stmt = stmt.join(
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
        ).where(
            EventClusterMembership.cluster_id
            == filters.event_cluster_id
        )

    stmt = (
        stmt
        .order_by(
            Article.published_at.desc().nullslast(),
            Article.id.desc(),
        )
        .limit(limit)
    )

    articles = list(
        (await db.execute(stmt)).scalars().all()
    )

    enrichments = await get_search_result_enrichments(
        db,
        article_ids=[
            article.id
            for article in articles
        ],
        company_id=company_id,
    )

    return [
        KeywordSearchItem(
            article_id=article.id,
            title=article.title,
            source_name=article.source_name,
            url=article.url,
            published_at=article.published_at,
            event_type=(
                enrichments[article.id].event_type
                if article.id in enrichments
                else None
            ),
            sentiment=(
                enrichments[article.id].sentiment
                if article.id in enrichments
                else None
            ),
            risk_level=(
                enrichments[article.id].risk_level
                if article.id in enrichments
                else None
            ),
            risk_score=(
                enrichments[article.id].risk_score
                if article.id in enrichments
                else None
            ),
            business_impact=(
                enrichments[article.id].business_impact
                if article.id in enrichments
                else None
            ),
            event_cluster_id=(
                enrichments[article.id].event_cluster_id
                if article.id in enrichments
                else None
            ),
        )
        for article in articles
    ]


async def list_event_clusters(
    db: AsyncSession,
    *,
    company_id: int | None,
    limit: int = 50,
):
    stmt = (
        select(
            EventCluster,
            func.count(
                EventClusterMembership.article_id
            ).label("article_count"),
        )
        .outerjoin(
            EventClusterMembership,
            EventClusterMembership.cluster_id
            == EventCluster.id,
        )
        .group_by(EventCluster.id)
        .order_by(
            EventCluster.last_published_at
            .desc()
            .nullslast(),
            EventCluster.id.desc(),
        )
        .limit(limit)
    )

    if company_id is not None:
        stmt = stmt.where(
            EventCluster.company_id == company_id
        )

    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": cluster.id,
            "company_id": cluster.company_id,
            "title": cluster.title,
            "representative_article_id": (
                cluster.representative_article_id
            ),
            "first_published_at": (
                cluster.first_published_at
            ),
            "last_published_at": (
                cluster.last_published_at
            ),
            "article_count": article_count,
        }
        for cluster, article_count in rows
    ]


async def get_event_cluster_detail(
    db: AsyncSession,
    *,
    cluster_id: int,
    company_id: int | None = None,
):
    cluster_stmt = select(EventCluster).where(
        EventCluster.id == cluster_id
    )

    if company_id is not None:
        cluster_stmt = cluster_stmt.where(
            EventCluster.company_id == company_id
        )

    cluster = (
        await db.execute(cluster_stmt)
    ).scalar_one_or_none()

    if cluster is None:
        return None

    articles = (
        await db.execute(
            select(
                Article.id,
                Article.title,
                Article.source_name,
                Article.url,
                Article.published_at,
                EventClusterMembership.similarity,
            )
            .join(
                EventClusterMembership,
                EventClusterMembership.article_id
                == Article.id,
            )
            .where(
                EventClusterMembership.cluster_id
                == cluster_id
            )
            .order_by(
                Article.published_at
                .desc()
                .nullslast()
            )
        )
    ).all()

    return {
        "id": cluster.id,
        "company_id": cluster.company_id,
        "title": cluster.title,
        "representative_article_id": (
            cluster.representative_article_id
        ),
        "first_published_at": (
            cluster.first_published_at
        ),
        "last_published_at": (
            cluster.last_published_at
        ),
        "articles": [
            {
                "article_id": row.id,
                "title": row.title,
                "source_name": row.source_name,
                "url": row.url,
                "published_at": row.published_at,
                "similarity": row.similarity,
            }
            for row in articles
        ],
    }

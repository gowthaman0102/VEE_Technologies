from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.event_cluster import EventClusterMembership
from app.models.risk_assessment import RiskAssessment
from app.schemas.search_filters import SearchFilters
from app.services.search_enrichment_service import (
    get_search_result_enrichments,
)
from app.utils.article_metadata import publisher_name


@dataclass
class SemanticSearchResult:
    article_id: int
    title: str
    source_name: str
    url: str
    distance: float
    similarity: float
    published_at: datetime | None = None
    publisher_name: str = ""
    collected_at: datetime | None = None
    event_type: str | None = None
    sentiment: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None
    event_cluster_id: int | None = None


async def semantic_search(
    db: AsyncSession,
    query: str,
    *,
    limit: int = 10,
    minimum_similarity: float | None = None,
    company_id: int | None = None,
    provider: EmbeddingProvider | None = None,
    filters: SearchFilters | None = None,
) -> list[SemanticSearchResult]:
    normalized_query = query.strip()

    if not normalized_query:
        raise ValueError(
            "Semantic search query cannot be empty."
        )

    if limit < 1:
        raise ValueError(
            "Semantic search limit must be at least 1."
        )

    if minimum_similarity is not None and not (
        -1.0 <= minimum_similarity <= 1.0
    ):
        raise ValueError(
            "Minimum similarity must be between -1 and 1."
        )

    filters = filters or SearchFilters()

    company_scoped_filter_requested = any(
        value is not None
        for value in (
            filters.sentiment,
            filters.risk_level,
            filters.business_impact,
            filters.event_type,
            filters.event_cluster_id,
        )
    )

    if (
        company_scoped_filter_requested
        and company_id is None
    ):
        raise ValueError(
            "company_id is required for company-scoped "
            "semantic search filters."
        )

    embedding_provider = (
        provider
        if provider is not None
        else get_embedding_provider()
    )

    query_embedding = await embedding_provider.embed_text(
        normalized_query
    )

    distance_expression = (
        Article.embedding.cosine_distance(
            query_embedding.vector
        )
    )

    statement = (
        select(
            Article.id,
            Article.title,
            Article.source_name,
            Article.url,
            Article.published_at,
            Article.collected_at,
            distance_expression.label(
                "distance"
            ),
        )
        .where(
            Article.embedding_status == "success",
            Article.embedding.is_not(None),
        )
    )

    if company_id is not None:
        statement = statement.join(
            ArticleTriage,
            ArticleTriage.article_id == Article.id,
        ).where(
            ArticleTriage.company_id == company_id
        )

    if filters.start is not None:
        statement = statement.where(
            Article.published_at >= filters.start
        )

    if filters.end is not None:
        statement = statement.where(
            Article.published_at <= filters.end
        )

    if filters.source_name is not None:
        statement = statement.where(
            func.lower(Article.source_name)
            == filters.source_name.lower()
        )

    if filters.event_type is not None:
        statement = statement.where(
            func.lower(ArticleTriage.event_type)
            == filters.event_type.lower()
        )

    if filters.sentiment is not None:
        statement = statement.join(
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
        statement = statement.join(
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
        statement = statement.join(
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
        statement = statement.join(
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

    statement = (
        statement
        .order_by(
            distance_expression.asc()
        )
        .limit(limit)
    )

    result = await db.execute(statement)

    search_results: list[
        SemanticSearchResult
    ] = []

    for row in result.all():
        distance = float(row.distance)
        similarity = 1.0 - distance

        if (
            minimum_similarity is not None
            and similarity < minimum_similarity
        ):
            continue

        search_results.append(
            SemanticSearchResult(
                article_id=row.id,
                title=row.title,
                publisher_name=publisher_name(
                    row.source_name,
                    row.title,
                    row.url,
                ),
                source_name=row.source_name,
                url=row.url,
                published_at=row.published_at,
                collected_at=row.collected_at,
                distance=distance,
                similarity=similarity,
            )
        )

    if company_id is None or not search_results:
        return search_results

    enrichments = await get_search_result_enrichments(
        db,
        article_ids=[
            item.article_id
            for item in search_results
        ],
        company_id=company_id,
    )

    return [
        SemanticSearchResult(
            article_id=item.article_id,
            title=item.title,
            publisher_name=item.publisher_name,
            source_name=item.source_name,
            url=item.url,
            published_at=item.published_at,
            collected_at=item.collected_at,
            distance=item.distance,
            similarity=item.similarity,
            event_type=(
                enrichments[item.article_id].event_type
                if item.article_id in enrichments
                else None
            ),
            sentiment=(
                enrichments[item.article_id].sentiment
                if item.article_id in enrichments
                else None
            ),
            risk_level=(
                enrichments[item.article_id].risk_level
                if item.article_id in enrichments
                else None
            ),
            risk_score=(
                enrichments[item.article_id].risk_score
                if item.article_id in enrichments
                else None
            ),
            business_impact=(
                enrichments[item.article_id].business_impact
                if item.article_id in enrichments
                else None
            ),
            event_cluster_id=(
                enrichments[item.article_id].event_cluster_id
                if item.article_id in enrichments
                else None
            ),
        )
        for item in search_results
    ]

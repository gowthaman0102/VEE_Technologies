from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.embeddings import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.models.article import Article
from app.services.company_semantic_context_service import (
    build_company_semantic_context,
)


@dataclass
class ArticleRelevanceResult:
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None
    distance: float
    similarity: float
    is_relevant: bool


@dataclass
class CompanyRelevanceResult:
    company_id: int
    company_name: str
    threshold: float
    context_text: str
    results: list[ArticleRelevanceResult]


async def score_company_article_relevance(
    db: AsyncSession,
    company_id: int,
    *,
    limit: int = 50,
    threshold: float | None = None,
    provider: EmbeddingProvider | None = None,
) -> CompanyRelevanceResult | None:
    if limit < 1:
        raise ValueError(
            "Relevance result limit must be at least 1."
        )

    resolved_threshold = (
        settings.semantic_relevance_threshold
        if threshold is None
        else threshold
    )

    if not -1.0 <= resolved_threshold <= 1.0:
        raise ValueError(
            "Semantic relevance threshold must be "
            "between -1 and 1."
        )

    company_context = (
        await build_company_semantic_context(
            db,
            company_id,
        )
    )

    if company_context is None:
        return None

    embedding_provider = (
        provider
        if provider is not None
        else get_embedding_provider()
    )

    context_embedding = (
        await embedding_provider.embed_text(
            company_context.text
        )
    )

    distance_expression = (
        Article.embedding.cosine_distance(
            context_embedding.vector
        )
    )

    statement = (
        select(
            Article.id,
            Article.title,
            Article.source_name,
            Article.url,
            Article.published_at,
            distance_expression.label(
                "distance"
            ),
        )
        .where(
            Article.embedding_status == "success",
            Article.embedding.is_not(None),
        )
        .order_by(
            distance_expression.asc(),
            Article.id.asc(),
        )
        .limit(limit)
    )

    result = await db.execute(statement)

    relevance_results = []

    for row in result.all():
        distance = float(row.distance)
        similarity = 1.0 - distance

        relevance_results.append(
            ArticleRelevanceResult(
                article_id=row.id,
                title=row.title,
                source_name=row.source_name,
                url=row.url,
                published_at=row.published_at,
                distance=distance,
                similarity=similarity,
                is_relevant=(
                    similarity
                    >= resolved_threshold
                ),
            )
        )

    return CompanyRelevanceResult(
        company_id=company_context.company_id,
        company_name=(
            company_context.company_name
        ),
        threshold=resolved_threshold,
        context_text=company_context.text,
        results=relevance_results,
    )

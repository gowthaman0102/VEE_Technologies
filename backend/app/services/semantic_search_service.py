from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.models.article import Article
from app.models.article_triage import ArticleTriage


@dataclass
class SemanticSearchResult:
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None
    distance: float
    similarity: float


async def semantic_search(
    db: AsyncSession,
    query: str,
    *,
    limit: int = 10,
    minimum_similarity: float | None = None,
    company_id: int | None = None,
    provider: EmbeddingProvider | None = None,
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
            distance_expression.label(
                "distance"
            ),
        )
        .where(
            Article.embedding_status == "success",
            Article.embedding.is_not(None),
        )
        .order_by(
            distance_expression.asc()
        )
        .limit(limit)
    )

    if company_id is not None:
        statement = statement.join(
            ArticleTriage,
            ArticleTriage.article_id == Article.id,
        ).where(ArticleTriage.company_id == company_id)

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
                source_name=row.source_name,
                url=row.url,
                published_at=row.published_at,
                distance=distance,
                similarity=similarity,
            )
        )

    return search_results

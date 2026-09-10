from dataclasses import dataclass

from app.embeddings import EmbeddingProvider
from app.models.article import Article
from app.services.semantic_search_service import (
    SemanticSearchResult,
    semantic_search,
)


@dataclass
class RAGContext:
    query: str
    related_articles: list[SemanticSearchResult]


def build_rag_query(
    article: Article,
    company_name: str,
) -> str:
    title = (article.title or "").strip()

    if not title:
        raise ValueError(
            "Article title is required for RAG retrieval."
        )

    return f"{company_name}: {title}"


async def retrieve_rag_context(
    db,
    article: Article,
    company_name: str,
    *,
    limit: int = 3,
    provider: EmbeddingProvider | None = None,
) -> RAGContext:
    if limit < 1:
        raise ValueError(
            "RAG retrieval limit must be at least 1."
        )

    query = build_rag_query(
        article,
        company_name,
    )

    results = await semantic_search(
        db,
        query=query,
        limit=limit + 1,
        provider=provider,
    )

    related = [
        item
        for item in results
        if item.article_id != article.id
    ][:limit]

    return RAGContext(
        query=query,
        related_articles=related,
    )

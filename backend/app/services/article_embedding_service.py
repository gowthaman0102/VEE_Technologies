from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.models.article import Article
from app.services.article_service import get_article


@dataclass
class ArticleEmbeddingResult:
    article_id: int
    status: str
    model: str | None = None
    dimensions: int | None = None
    error: str | None = None


async def embed_article(
    db: AsyncSession,
    article: Article,
    *,
    provider: EmbeddingProvider | None = None,
) -> ArticleEmbeddingResult:
    if article.extraction_status != "success":
        article.embedding = None
        article.embedding_model = None
        article.embedding_status = "skipped"
        article.embedding_error = (
            "Article extraction must be successful before embedding."
        )
        article.embedded_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(article)

        return ArticleEmbeddingResult(
            article_id=article.id,
            status="skipped",
            error=article.embedding_error,
        )

    cleaned_content = (article.cleaned_content or "").strip()

    if not cleaned_content:
        article.embedding = None
        article.embedding_model = None
        article.embedding_status = "skipped"
        article.embedding_error = (
            "Article cleaned content is empty."
        )
        article.embedded_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(article)

        return ArticleEmbeddingResult(
            article_id=article.id,
            status="skipped",
            error=article.embedding_error,
        )

    embedding_provider = provider or get_embedding_provider()

    try:
        result = await embedding_provider.embed_text(
            cleaned_content
        )
    except Exception as exc:
        article.embedding = None
        article.embedding_model = None
        article.embedding_status = "failed"
        article.embedding_error = (
            f"Embedding generation failed: "
            f"{type(exc).__name__}"
        )
        article.embedded_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(article)

        return ArticleEmbeddingResult(
            article_id=article.id,
            status="failed",
            error=article.embedding_error,
        )

    article.embedding = result.vector
    article.embedding_model = result.model
    article.embedding_status = "success"
    article.embedding_error = None
    article.embedded_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(article)

    return ArticleEmbeddingResult(
        article_id=article.id,
        status="success",
        model=result.model,
        dimensions=result.dimensions,
    )


async def embed_article_by_id(
    db: AsyncSession,
    article_id: int,
    *,
    provider: EmbeddingProvider | None = None,
) -> ArticleEmbeddingResult | None:
    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        return None

    return await embed_article(
        db,
        article,
        provider=provider,
    )

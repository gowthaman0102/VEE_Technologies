from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.embeddings import EmbeddingResult
from app.models.article import Article
from app.services.article_embedding_service import embed_article


def make_article(
    *,
    article_id: int = 1,
    extraction_status: str = "success",
    cleaned_content: str | None = "PayU expands payments platform in India.",
) -> Article:
    return Article(
        id=article_id,
        source_name="test-source",
        source_type="rss",
        title="Test article",
        url="https://example.com/article",
        extraction_status=extraction_status,
        cleaned_content=cleaned_content,
        embedding_status="pending",
    )


@pytest.mark.asyncio
async def test_embed_article_success():
    db = AsyncMock()

    provider = SimpleNamespace(
        embed_text=AsyncMock(
            return_value=EmbeddingResult(
                vector=[0.1, 0.2, 0.3],
                model="test-model",
                dimensions=3,
            )
        )
    )

    article = make_article()

    result = await embed_article(
        db,
        article,
        provider=provider,
    )

    assert result.article_id == 1
    assert result.status == "success"
    assert result.model == "test-model"
    assert result.dimensions == 3
    assert result.error is None

    assert article.embedding == [0.1, 0.2, 0.3]
    assert article.embedding_model == "test-model"
    assert article.embedding_status == "success"
    assert article.embedding_error is None
    assert article.embedded_at is not None

    provider.embed_text.assert_awaited_once_with(
        "PayU expands payments platform in India."
    )

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(article)


@pytest.mark.asyncio
async def test_embed_article_skips_unsuccessful_extraction():
    db = AsyncMock()
    provider = SimpleNamespace(
        embed_text=AsyncMock()
    )

    article = make_article(
        extraction_status="failed"
    )

    result = await embed_article(
        db,
        article,
        provider=provider,
    )

    assert result.status == "skipped"
    assert article.embedding_status == "skipped"
    assert article.embedding is None
    assert article.embedding_model is None
    assert article.embedding_error is not None
    assert article.embedded_at is not None

    provider.embed_text.assert_not_awaited()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(article)


@pytest.mark.asyncio
async def test_embed_article_skips_empty_cleaned_content():
    db = AsyncMock()
    provider = SimpleNamespace(
        embed_text=AsyncMock()
    )

    article = make_article(
        cleaned_content="   "
    )

    result = await embed_article(
        db,
        article,
        provider=provider,
    )

    assert result.status == "skipped"
    assert article.embedding_status == "skipped"
    assert "empty" in article.embedding_error.lower()

    provider.embed_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_embed_article_records_provider_failure():
    db = AsyncMock()

    provider = SimpleNamespace(
        embed_text=AsyncMock(
            side_effect=RuntimeError(
                "provider unavailable"
            )
        )
    )

    article = make_article()

    result = await embed_article(
        db,
        article,
        provider=provider,
    )

    assert result.status == "failed"
    assert article.embedding_status == "failed"
    assert article.embedding is None
    assert article.embedding_model is None
    assert (
        article.embedding_error
        == "Embedding generation failed: RuntimeError"
    )
    assert article.embedded_at is not None

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(article)


@pytest.mark.asyncio
async def test_embed_article_trims_cleaned_content():
    db = AsyncMock()

    provider = SimpleNamespace(
        embed_text=AsyncMock(
            return_value=EmbeddingResult(
                vector=[0.1],
                model="test-model",
                dimensions=1,
            )
        )
    )

    article = make_article(
        cleaned_content="  PayU regulation  "
    )

    await embed_article(
        db,
        article,
        provider=provider,
    )

    provider.embed_text.assert_awaited_once_with(
        "PayU regulation"
    )

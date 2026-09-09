from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.article import Article
from app.services.article_embedding_service import (
    ArticleEmbeddingResult,
)
from app.services.article_embedding_batch_service import (
    get_embeddable_articles,
    process_embedding_batch,
)


def make_article(
    article_id: int,
    *,
    embedding_status: str = "pending",
) -> Article:
    return Article(
        id=article_id,
        source_name="test-source",
        source_type="rss",
        title=f"Article {article_id}",
        url=f"https://example.com/{article_id}",
        extraction_status="success",
        cleaned_content="PayU payments in India",
        embedding_status=embedding_status,
    )


@pytest.mark.asyncio
async def test_get_embeddable_articles_returns_query_results():
    articles = [
        make_article(1),
        make_article(2),
    ]

    scalars = SimpleNamespace(
        all=lambda: articles
    )

    execute_result = SimpleNamespace(
        scalars=lambda: scalars
    )

    db = AsyncMock()
    db.execute.return_value = execute_result

    result = await get_embeddable_articles(
        db,
        limit=2,
    )

    assert result == articles
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_embeddable_articles_rejects_invalid_limit():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Batch limit must be at least 1",
    ):
        await get_embeddable_articles(
            db,
            limit=0,
        )

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_embedding_batch_counts_results(
    monkeypatch,
):
    articles = [
        make_article(1),
        make_article(2),
        make_article(3),
    ]

    get_articles = AsyncMock(
        return_value=articles
    )

    embed = AsyncMock(
        side_effect=[
            ArticleEmbeddingResult(
                article_id=1,
                status="success",
                model="test-model",
                dimensions=3,
            ),
            ArticleEmbeddingResult(
                article_id=2,
                status="skipped",
                error="Skipped",
            ),
            ArticleEmbeddingResult(
                article_id=3,
                status="failed",
                error="Failed",
            ),
        ]
    )

    monkeypatch.setattr(
        "app.services.article_embedding_batch_service."
        "get_embeddable_articles",
        get_articles,
    )

    monkeypatch.setattr(
        "app.services.article_embedding_batch_service."
        "embed_article",
        embed,
    )

    db = AsyncMock()
    provider = SimpleNamespace()

    result = await process_embedding_batch(
        db,
        limit=3,
        provider=provider,
    )

    assert result.selected == 3
    assert result.success == 1
    assert result.skipped == 1
    assert result.failed == 1
    assert len(result.results) == 3

    get_articles.assert_awaited_once_with(
        db,
        limit=3,
        include_failed=False,
    )

    assert embed.await_count == 3


@pytest.mark.asyncio
async def test_process_embedding_batch_forwards_retry_option(
    monkeypatch,
):
    get_articles = AsyncMock(
        return_value=[]
    )

    monkeypatch.setattr(
        "app.services.article_embedding_batch_service."
        "get_embeddable_articles",
        get_articles,
    )

    db = AsyncMock()

    result = await process_embedding_batch(
        db,
        limit=5,
        include_failed=True,
        provider=SimpleNamespace(),
    )

    assert result.selected == 0

    get_articles.assert_awaited_once_with(
        db,
        limit=5,
        include_failed=True,
    )


@pytest.mark.asyncio
async def test_process_embedding_batch_isolates_unexpected_failure(
    monkeypatch,
):
    articles = [
        make_article(10),
        make_article(11),
    ]

    get_articles = AsyncMock(
        return_value=articles
    )

    embed = AsyncMock(
        side_effect=[
            RuntimeError("unexpected failure"),
            ArticleEmbeddingResult(
                article_id=11,
                status="success",
                model="test-model",
                dimensions=3,
            ),
        ]
    )

    monkeypatch.setattr(
        "app.services.article_embedding_batch_service."
        "get_embeddable_articles",
        get_articles,
    )

    monkeypatch.setattr(
        "app.services.article_embedding_batch_service."
        "embed_article",
        embed,
    )

    db = AsyncMock()

    result = await process_embedding_batch(
        db,
        limit=2,
        provider=SimpleNamespace(),
    )

    assert result.selected == 2
    assert result.success == 1
    assert result.failed == 1
    assert result.skipped == 0

    assert result.results[0].article_id == 10
    assert result.results[0].status == "failed"
    assert (
        result.results[0].error
        == "Embedding pipeline error: RuntimeError"
    )

    assert result.results[1].status == "success"

    db.rollback.assert_awaited_once()
    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()

    assert embed.await_count == 2


@pytest.mark.asyncio
async def test_process_embedding_batch_rejects_invalid_limit():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Batch limit must be at least 1",
    ):
        await process_embedding_batch(
            db,
            limit=0,
            provider=SimpleNamespace(),
        )

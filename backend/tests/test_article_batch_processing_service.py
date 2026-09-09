from unittest.mock import AsyncMock

import pytest

from app.models.article import Article
from app.services import (
    article_batch_processing_service as service,
)
from app.services.article_processing_service import (
    ArticleProcessingResult,
)


def make_article(
    article_id: int,
) -> Article:
    return Article(
        id=article_id,
        source_name="Test Source",
        source_type="rss",
        external_id=f"batch-{article_id}",
        title=f"Article {article_id}",
        url=(
            "https://example.com/"
            f"article-{article_id}"
        ),
        extraction_status="pending",
    )


@pytest.mark.asyncio
async def test_process_batch_counts_results(
    monkeypatch,
):
    db = AsyncMock()

    articles = [
        make_article(1),
        make_article(2),
        make_article(3),
    ]

    monkeypatch.setattr(
        service,
        "get_processable_articles",
        AsyncMock(
            return_value=articles
        ),
    )

    monkeypatch.setattr(
        service,
        "process_article",
        AsyncMock(
            side_effect=[
                ArticleProcessingResult(
                    article_id=1,
                    status="success",
                ),
                ArticleProcessingResult(
                    article_id=2,
                    status="skipped",
                    duplicate_of_id=1,
                ),
                ArticleProcessingResult(
                    article_id=3,
                    status="failed",
                    error="fetch failed",
                ),
            ]
        ),
    )

    result = await service.process_articles_batch(
        db,
        limit=3,
    )

    assert result.selected == 3
    assert result.success == 1
    assert result.skipped == 1
    assert result.failed == 1
    assert len(result.results) == 3


@pytest.mark.asyncio
async def test_process_batch_isolates_exception(
    monkeypatch,
):
    db = AsyncMock()

    articles = [
        make_article(10),
        make_article(11),
    ]

    monkeypatch.setattr(
        service,
        "get_processable_articles",
        AsyncMock(
            return_value=articles
        ),
    )

    monkeypatch.setattr(
        service,
        "process_article",
        AsyncMock(
            side_effect=[
                RuntimeError("boom"),
                ArticleProcessingResult(
                    article_id=11,
                    status="success",
                ),
            ]
        ),
    )

    result = await service.process_articles_batch(
        db,
        limit=2,
    )

    assert result.selected == 2
    assert result.success == 1
    assert result.failed == 1

    assert (
        result.results[0].article_id
        == 10
    )

    assert (
        result.results[0].status
        == "failed"
    )

    assert (
        "RuntimeError"
        in result.results[0].error
    )

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_batch_empty(
    monkeypatch,
):
    db = AsyncMock()

    monkeypatch.setattr(
        service,
        "get_processable_articles",
        AsyncMock(return_value=[]),
    )

    result = await service.process_articles_batch(
        db
    )

    assert result.selected == 0
    assert result.success == 0
    assert result.skipped == 0
    assert result.failed == 0
    assert result.results == []


@pytest.mark.asyncio
async def test_process_batch_invalid_limit():
    db = AsyncMock()

    with pytest.raises(ValueError):
        await service.process_articles_batch(
            db,
            limit=0,
        )

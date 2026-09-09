from unittest.mock import AsyncMock

import pytest

from app.models.article import Article
from app.processing.extractor import ExtractionResult
from app.services import article_processing_service as service


def make_article(
    article_id: int = 100,
) -> Article:
    return Article(
        id=article_id,
        source_name="Test Source",
        source_type="rss",
        external_id=f"test-{article_id}",
        title="PayU test article",
        url=(
            "https://example.com/article"
            "?utm_source=newsletter"
        ),
        language="en",
        extraction_status="pending",
    )


@pytest.mark.asyncio
async def test_process_article_success(
    monkeypatch,
):
    article = make_article()
    db = AsyncMock()

    extractor = AsyncMock()
    extractor.extract_from_url.return_value = (
        ExtractionResult(
            success=True,
            content=(
                "PayU regulatory article "
                "content."
            ),
            error=None,
            final_url=(
                "https://example.com/article"
            ),
        )
    )

    monkeypatch.setattr(
        service,
        "find_canonical_duplicate",
        AsyncMock(return_value=None),
    )

    monkeypatch.setattr(
        service,
        "find_content_duplicate",
        AsyncMock(return_value=None),
    )

    result = await service.process_article(
        db,
        article,
        extractor=extractor,
    )

    assert result.status == "success"
    assert result.content_hash is not None
    assert len(result.content_hash) == 64

    assert article.canonical_url == (
        "https://example.com/article"
    )
    assert article.cleaned_content == (
        "PayU regulatory article content."
    )
    assert article.extraction_status == (
        "success"
    )
    assert article.extraction_error is None
    assert article.processed_at is not None

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        article
    )


@pytest.mark.asyncio
async def test_process_article_fetch_failure(
    monkeypatch,
):
    article = make_article()
    db = AsyncMock()

    extractor = AsyncMock()
    extractor.extract_from_url.return_value = (
        ExtractionResult(
            success=False,
            content=None,
            error="Article fetch timed out",
        )
    )

    monkeypatch.setattr(
        service,
        "find_canonical_duplicate",
        AsyncMock(return_value=None),
    )

    result = await service.process_article(
        db,
        article,
        extractor=extractor,
    )

    assert result.status == "failed"
    assert result.error == (
        "Article fetch timed out"
    )
    assert article.extraction_status == (
        "failed"
    )
    assert article.processed_at is not None

    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_article_skips_canonical_duplicate(
    monkeypatch,
):
    article = make_article()
    duplicate = make_article(
        article_id=50
    )

    db = AsyncMock()
    extractor = AsyncMock()

    monkeypatch.setattr(
        service,
        "find_canonical_duplicate",
        AsyncMock(return_value=duplicate),
    )

    result = await service.process_article(
        db,
        article,
        extractor=extractor,
    )

    assert result.status == "skipped"
    assert result.duplicate_of_id == 50

    assert article.extraction_status == (
        "skipped"
    )

    extractor.extract_from_url.assert_not_awaited()

    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_article_skips_content_duplicate(
    monkeypatch,
):
    article = make_article()
    duplicate = make_article(
        article_id=60
    )

    db = AsyncMock()

    extractor = AsyncMock()
    extractor.extract_from_url.return_value = (
        ExtractionResult(
            success=True,
            content="Identical article content",
            error=None,
            final_url=(
                "https://example.com/article"
            ),
        )
    )

    canonical_mock = AsyncMock(
        side_effect=[
            None,
            None,
        ]
    )

    monkeypatch.setattr(
        service,
        "find_canonical_duplicate",
        canonical_mock,
    )

    monkeypatch.setattr(
        service,
        "find_content_duplicate",
        AsyncMock(
            return_value=duplicate
        ),
    )

    result = await service.process_article(
        db,
        article,
        extractor=extractor,
    )

    assert result.status == "skipped"
    assert result.duplicate_of_id == 60
    assert result.content_hash is not None

    assert article.extraction_status == (
        "skipped"
    )
    assert article.cleaned_content == (
        "Identical article content"
    )

    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_article_by_id_missing(
    monkeypatch,
):
    db = AsyncMock()

    monkeypatch.setattr(
        service,
        "get_article",
        AsyncMock(return_value=None),
    )

    result = (
        await service.process_article_by_id(
            db,
            article_id=999999,
        )
    )

    assert result is None

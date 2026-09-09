from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.ingestion.types import CollectedArticle
from app.services import article_service


def make_article():
    return CollectedArticle(
        source_name="Test Provider",
        source_type="rss",
        external_id="provider-001",
        title="PayU regulatory update",
        url="https://example.com/provider-001",
        language="en",
    )


@pytest.mark.asyncio
async def test_save_collected_article_inserts_new(
    monkeypatch,
):
    data = make_article()
    created_article = object()

    find_mock = AsyncMock(
        return_value=None
    )

    create_mock = AsyncMock(
        return_value=created_article
    )

    monkeypatch.setattr(
        article_service,
        "find_existing_article",
        find_mock,
    )

    monkeypatch.setattr(
        article_service,
        "create_article",
        create_mock,
    )

    db = AsyncMock()

    article, created = (
        await article_service.save_collected_article(
            db,
            data,
        )
    )

    assert article is created_article
    assert created is True
    assert find_mock.await_count == 1
    assert create_mock.await_count == 1
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_collected_article_skips_existing(
    monkeypatch,
):
    data = make_article()
    existing_article = object()

    find_mock = AsyncMock(
        return_value=existing_article
    )

    create_mock = AsyncMock()

    monkeypatch.setattr(
        article_service,
        "find_existing_article",
        find_mock,
    )

    monkeypatch.setattr(
        article_service,
        "create_article",
        create_mock,
    )

    db = AsyncMock()

    article, created = (
        await article_service.save_collected_article(
            db,
            data,
        )
    )

    assert article is existing_article
    assert created is False
    assert find_mock.await_count == 1
    create_mock.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_collected_article_recovers_duplicate_race(
    monkeypatch,
):
    data = make_article()
    winning_article = object()

    find_mock = AsyncMock(
        side_effect=[
            None,
            winning_article,
        ]
    )

    create_mock = AsyncMock(
        side_effect=IntegrityError(
            "duplicate provider identity",
            {},
            Exception("unique violation"),
        )
    )

    monkeypatch.setattr(
        article_service,
        "find_existing_article",
        find_mock,
    )

    monkeypatch.setattr(
        article_service,
        "create_article",
        create_mock,
    )

    db = AsyncMock()

    article, created = (
        await article_service.save_collected_article(
            db,
            data,
        )
    )

    assert article is winning_article
    assert created is False
    assert find_mock.await_count == 2
    assert create_mock.await_count == 1
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_collected_article_reraises_unrelated_integrity_error(
    monkeypatch,
):
    data = make_article()

    find_mock = AsyncMock(
        side_effect=[
            None,
            None,
        ]
    )

    create_mock = AsyncMock(
        side_effect=IntegrityError(
            "other integrity error",
            {},
            Exception("database constraint"),
        )
    )

    monkeypatch.setattr(
        article_service,
        "find_existing_article",
        find_mock,
    )

    monkeypatch.setattr(
        article_service,
        "create_article",
        create_mock,
    )

    db = AsyncMock()

    with pytest.raises(IntegrityError):
        await article_service.save_collected_article(
            db,
            data,
        )

    db.rollback.assert_awaited_once()
    assert find_mock.await_count == 2


@pytest.mark.asyncio
async def test_null_external_id_integrity_error_is_reraised(
    monkeypatch,
):
    data = CollectedArticle(
        source_name="Test Provider",
        source_type="rss",
        external_id=None,
        title="Article without provider ID",
        url="https://example.com/no-id",
    )

    find_mock = AsyncMock(
        return_value=None
    )

    create_mock = AsyncMock(
        side_effect=IntegrityError(
            "integrity error",
            {},
            Exception("database constraint"),
        )
    )

    monkeypatch.setattr(
        article_service,
        "find_existing_article",
        find_mock,
    )

    monkeypatch.setattr(
        article_service,
        "create_article",
        create_mock,
    )

    db = AsyncMock()

    with pytest.raises(IntegrityError):
        await article_service.save_collected_article(
            db,
            data,
        )

    db.rollback.assert_awaited_once()
    assert find_mock.await_count == 1

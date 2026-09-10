from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.article_triage_service import ArticleNotFoundError

from app.services.article_triage_batch_service import (
    triage_articles_batch,
)


def make_result(article_id: int):
    return SimpleNamespace(
        article_id=article_id,
        model="test-llm",
        triage=SimpleNamespace(
            company_name="PayU"
        ),
    )


@pytest.mark.asyncio
async def test_batch_triage_all_success(monkeypatch):
    triage_mock = AsyncMock(
        side_effect=[
            make_result(1),
            make_result(2),
            make_result(3),
        ]
    )

    monkeypatch.setattr(
        "app.services.article_triage_batch_service."
        "triage_article",
        triage_mock,
    )

    result = await triage_articles_batch(
        AsyncMock(),
        article_ids=[1, 2, 3],
        company_id=1,
    )

    assert result.company_id == 1
    assert result.requested_count == 3
    assert result.success_count == 3
    assert result.not_found_count == 0
    assert result.failed_count == 0

    assert [
        item.status
        for item in result.items
    ] == [
        "success",
        "success",
        "success",
    ]


@pytest.mark.asyncio
async def test_batch_triage_handles_not_found(
    monkeypatch,
):
    triage_mock = AsyncMock(
        side_effect=[
            make_result(1),
            ArticleNotFoundError(
                "Article 999 not found."
            ),
        ]
    )

    monkeypatch.setattr(
        "app.services.article_triage_batch_service."
        "triage_article",
        triage_mock,
    )

    result = await triage_articles_batch(
        AsyncMock(),
        article_ids=[1, 999],
        company_id=1,
    )

    assert result.requested_count == 2
    assert result.success_count == 1
    assert result.not_found_count == 1
    assert result.failed_count == 0

    assert result.items[1].status == "not_found"
    assert result.items[1].result is None


@pytest.mark.asyncio
async def test_batch_triage_isolates_failures(
    monkeypatch,
):
    triage_mock = AsyncMock(
        side_effect=[
            make_result(1),
            ValueError("LLM returned invalid JSON."),
            make_result(3),
        ]
    )

    monkeypatch.setattr(
        "app.services.article_triage_batch_service."
        "triage_article",
        triage_mock,
    )

    result = await triage_articles_batch(
        AsyncMock(),
        article_ids=[1, 2, 3],
        company_id=1,
    )

    assert result.requested_count == 3
    assert result.success_count == 2
    assert result.failed_count == 1

    failed = result.items[1]

    assert failed.article_id == 2
    assert failed.status == "failed"
    assert failed.error == (
        "LLM returned invalid JSON."
    )


@pytest.mark.asyncio
async def test_batch_triage_removes_duplicate_ids(
    monkeypatch,
):
    triage_mock = AsyncMock(
        side_effect=[
            make_result(1),
            make_result(2),
        ]
    )

    monkeypatch.setattr(
        "app.services.article_triage_batch_service."
        "triage_article",
        triage_mock,
    )

    result = await triage_articles_batch(
        AsyncMock(),
        article_ids=[1, 1, 2, 2],
        company_id=1,
    )

    assert result.requested_count == 2
    assert result.success_count == 2
    assert len(result.items) == 2
    assert triage_mock.await_count == 2


@pytest.mark.asyncio
async def test_batch_triage_rejects_empty_ids():
    with pytest.raises(
        ValueError,
        match="At least one article ID is required",
    ):
        await triage_articles_batch(
            AsyncMock(),
            article_ids=[],
            company_id=1,
        )


@pytest.mark.asyncio
async def test_batch_triage_rejects_invalid_company():
    with pytest.raises(
        ValueError,
        match="Company ID must be at least 1",
    ):
        await triage_articles_batch(
            AsyncMock(),
            article_ids=[1],
            company_id=0,
        )

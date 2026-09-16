from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import (
    event_cluster_candidate_service,
)


def make_article(
    *,
    article_id=100,
    embedding_status="success",
    embedding=None,
):
    if embedding is None:
        embedding = [0.1] * 384

    return SimpleNamespace(
        id=article_id,
        embedding_status=embedding_status,
        embedding=embedding,
        published_at=datetime(
            2026,
            9,
            16,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        collected_at=datetime(
            2026,
            9,
            16,
            10,
            5,
            tzinfo=timezone.utc,
        ),
    )


@pytest.mark.asyncio
async def test_returns_candidates_above_threshold(
    monkeypatch,
):
    article = make_article()

    monkeypatch.setattr(
        event_cluster_candidate_service,
        "get_article",
        AsyncMock(return_value=article),
    )

    db = AsyncMock()

    result_mock = SimpleNamespace(
        all=lambda: [
            SimpleNamespace(
                cluster_id=7,
                article_id=90,
                distance=0.08,
            ),
            SimpleNamespace(
                cluster_id=8,
                article_id=91,
                distance=0.15,
            ),
        ]
    )

    db.execute.return_value = result_mock

    candidates = await (
        event_cluster_candidate_service
        .find_event_cluster_candidates(
            db,
            article_id=100,
            company_id=2,
            minimum_similarity=0.80,
            time_window_hours=48,
        )
    )

    assert len(candidates) == 2

    assert candidates[0].cluster_id == 7
    assert candidates[0].article_id == 90
    assert candidates[0].similarity == pytest.approx(
        0.92
    )

    assert candidates[1].cluster_id == 8
    assert candidates[1].article_id == 91
    assert candidates[1].similarity == pytest.approx(
        0.85
    )


@pytest.mark.asyncio
async def test_filters_candidate_below_threshold(
    monkeypatch,
):
    article = make_article()

    monkeypatch.setattr(
        event_cluster_candidate_service,
        "get_article",
        AsyncMock(return_value=article),
    )

    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: [
            SimpleNamespace(
                cluster_id=7,
                article_id=90,
                distance=0.08,
            ),
            SimpleNamespace(
                cluster_id=8,
                article_id=91,
                distance=0.30,
            ),
        ]
    )

    candidates = await (
        event_cluster_candidate_service
        .find_event_cluster_candidates(
            db,
            article_id=100,
            company_id=2,
            minimum_similarity=0.80,
            time_window_hours=48,
        )
    )

    assert len(candidates) == 1
    assert candidates[0].cluster_id == 7
    assert candidates[0].article_id == 90


@pytest.mark.asyncio
async def test_missing_article_returns_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        event_cluster_candidate_service,
        "get_article",
        AsyncMock(return_value=None),
    )

    db = AsyncMock()

    candidates = await (
        event_cluster_candidate_service
        .find_event_cluster_candidates(
            db,
            article_id=999,
            company_id=2,
            minimum_similarity=0.80,
            time_window_hours=48,
        )
    )

    assert candidates == []
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_article_without_embedding_returns_empty(
    monkeypatch,
):
    article = make_article(
        embedding_status="pending",
    )

    monkeypatch.setattr(
        event_cluster_candidate_service,
        "get_article",
        AsyncMock(return_value=article),
    )

    db = AsyncMock()

    candidates = await (
        event_cluster_candidate_service
        .find_event_cluster_candidates(
            db,
            article_id=100,
            company_id=2,
            minimum_similarity=0.80,
            time_window_hours=48,
        )
    )

    assert candidates == []
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_similarity_rejected():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Minimum similarity",
    ):
        await (
            event_cluster_candidate_service
            .find_event_cluster_candidates(
                db,
                article_id=100,
                company_id=2,
                minimum_similarity=1.5,
                time_window_hours=48,
            )
        )


@pytest.mark.asyncio
async def test_invalid_time_window_rejected():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Time window",
    ):
        await (
            event_cluster_candidate_service
            .find_event_cluster_candidates(
                db,
                article_id=100,
                company_id=2,
                minimum_similarity=0.80,
                time_window_hours=0,
            )
        )


@pytest.mark.asyncio
async def test_invalid_limit_rejected():
    db = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Candidate limit",
    ):
        await (
            event_cluster_candidate_service
            .find_event_cluster_candidates(
                db,
                article_id=100,
                company_id=2,
                minimum_similarity=0.80,
                time_window_hours=48,
                limit=0,
            )
        )

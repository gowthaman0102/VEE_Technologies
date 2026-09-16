from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock

import pytest

from app.services import (
    event_cluster_assignment_service,
)
from app.services.event_cluster_candidate_service import (
    EventClusterCandidate,
)


def make_article(
    *,
    article_id=100,
    title="Test Event",
):
    published_at = datetime(
        2026,
        9,
        16,
        10,
        0,
        tzinfo=timezone.utc,
    )

    return SimpleNamespace(
        id=article_id,
        title=title,
        published_at=published_at,
        collected_at=published_at,
    )


@pytest.mark.asyncio
async def test_existing_membership_is_reused(
    monkeypatch,
):
    article = make_article()

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_event_cluster_membership",
        AsyncMock(
            return_value=SimpleNamespace(
                cluster_id=7,
                similarity=0.93,
            )
        ),
    )

    candidate_mock = AsyncMock()

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "find_event_cluster_candidates",
        candidate_mock,
    )

    result = await (
        event_cluster_assignment_service
        .assign_article_to_event_cluster(
            AsyncMock(),
            article_id=100,
            company_id=2,
        )
    )

    assert result is not None
    assert result.cluster_id == 7
    assert result.created_new_cluster is False
    assert result.similarity == 0.93

    candidate_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_best_candidate_cluster_is_joined(
    monkeypatch,
):
    article = make_article()

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_event_cluster_membership",
        AsyncMock(return_value=None),
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "find_event_cluster_candidates",
        AsyncMock(
            return_value=[
                EventClusterCandidate(
                    cluster_id=4,
                    article_id=90,
                    similarity=0.84,
                ),
                EventClusterCandidate(
                    cluster_id=8,
                    article_id=91,
                    similarity=0.95,
                ),
            ]
        ),
    )

    membership_mock = AsyncMock(
        return_value=SimpleNamespace(
            cluster_id=8,
            similarity=0.95,
        )
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "upsert_event_cluster_membership",
        membership_mock,
    )

    create_mock = AsyncMock()

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "create_event_cluster",
        create_mock,
    )

    time_bounds_mock = AsyncMock()

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "update_event_cluster_time_bounds",
        time_bounds_mock,
    )

    result = await (
        event_cluster_assignment_service
        .assign_article_to_event_cluster(
            AsyncMock(),
            article_id=100,
            company_id=2,
        )
    )

    assert result is not None
    assert result.cluster_id == 8
    assert result.created_new_cluster is False
    assert result.similarity == 0.95

    create_mock.assert_not_awaited()

    time_bounds_mock.assert_awaited_once_with(
        ANY,
        cluster_id=8,
        article_time=article.published_at,
    )


@pytest.mark.asyncio
async def test_no_candidate_creates_new_cluster(
    monkeypatch,
):
    article = make_article()

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_article",
        AsyncMock(return_value=article),
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_event_cluster_membership",
        AsyncMock(return_value=None),
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "find_event_cluster_candidates",
        AsyncMock(return_value=[]),
    )

    cluster_mock = AsyncMock(
        return_value=SimpleNamespace(
            id=12,
        )
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "create_event_cluster",
        cluster_mock,
    )

    membership_mock = AsyncMock(
        return_value=SimpleNamespace(
            cluster_id=12,
            similarity=1.0,
        )
    )

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "upsert_event_cluster_membership",
        membership_mock,
    )

    result = await (
        event_cluster_assignment_service
        .assign_article_to_event_cluster(
            AsyncMock(),
            article_id=100,
            company_id=2,
        )
    )

    assert result is not None
    assert result.cluster_id == 12
    assert result.created_new_cluster is True
    assert result.similarity == 1.0

    cluster_mock.assert_awaited_once()

    membership_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_article_returns_none(
    monkeypatch,
):
    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_article",
        AsyncMock(return_value=None),
    )

    membership_mock = AsyncMock()

    monkeypatch.setattr(
        event_cluster_assignment_service,
        "get_event_cluster_membership",
        membership_mock,
    )

    result = await (
        event_cluster_assignment_service
        .assign_article_to_event_cluster(
            AsyncMock(),
            article_id=999,
            company_id=2,
        )
    )

    assert result is None
    membership_mock.assert_not_awaited()

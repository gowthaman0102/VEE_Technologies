from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.event_cluster import EventCluster
from app.services import (
    event_cluster_persistence_service,
)


@pytest.mark.asyncio
async def test_updates_first_published_at(
    monkeypatch,
):
    cluster = EventCluster(
        company_id=2,
        representative_article_id=100,
        title="Test Event",
        first_published_at=datetime(
            2026,
            9,
            16,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        last_published_at=datetime(
            2026,
            9,
            16,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    monkeypatch.setattr(
        event_cluster_persistence_service,
        "get_event_cluster",
        AsyncMock(return_value=cluster),
    )

    db = AsyncMock()

    earlier = datetime(
        2026,
        9,
        16,
        8,
        0,
        tzinfo=timezone.utc,
    )

    result = await (
        event_cluster_persistence_service
        .update_event_cluster_time_bounds(
            db,
            cluster_id=5,
            article_time=earlier,
        )
    )

    assert result is cluster
    assert cluster.first_published_at == earlier

    assert cluster.last_published_at == datetime(
        2026,
        9,
        16,
        12,
        0,
        tzinfo=timezone.utc,
    )

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(cluster)


@pytest.mark.asyncio
async def test_updates_last_published_at(
    monkeypatch,
):
    cluster = EventCluster(
        company_id=2,
        representative_article_id=100,
        title="Test Event",
        first_published_at=datetime(
            2026,
            9,
            16,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        last_published_at=datetime(
            2026,
            9,
            16,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    monkeypatch.setattr(
        event_cluster_persistence_service,
        "get_event_cluster",
        AsyncMock(return_value=cluster),
    )

    db = AsyncMock()

    later = datetime(
        2026,
        9,
        16,
        15,
        0,
        tzinfo=timezone.utc,
    )

    result = await (
        event_cluster_persistence_service
        .update_event_cluster_time_bounds(
            db,
            cluster_id=5,
            article_time=later,
        )
    )

    assert result is cluster
    assert cluster.last_published_at == later

    assert cluster.first_published_at == datetime(
        2026,
        9,
        16,
        10,
        0,
        tzinfo=timezone.utc,
    )

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(cluster)


@pytest.mark.asyncio
async def test_missing_cluster_returns_none(
    monkeypatch,
):
    monkeypatch.setattr(
        event_cluster_persistence_service,
        "get_event_cluster",
        AsyncMock(return_value=None),
    )

    db = AsyncMock()

    result = await (
        event_cluster_persistence_service
        .update_event_cluster_time_bounds(
            db,
            cluster_id=999,
            article_time=datetime.now(timezone.utc),
        )
    )

    assert result is None
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()

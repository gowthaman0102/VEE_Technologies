from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.event_cluster import (
    EventCluster,
    EventClusterMembership,
)
from app.services import (
    event_cluster_persistence_service,
)


@pytest.mark.asyncio
async def test_create_event_cluster():
    db = AsyncMock()
    db.add = Mock()

    published_at = datetime(
        2026,
        9,
        16,
        10,
        30,
        tzinfo=timezone.utc,
    )

    cluster = await (
        event_cluster_persistence_service
        .create_event_cluster(
            db,
            company_id=2,
            representative_article_id=100,
            title="Test Event",
            first_published_at=published_at,
            last_published_at=published_at,
        )
    )

    assert isinstance(
        cluster,
        EventCluster,
    )

    assert cluster.company_id == 2
    assert cluster.representative_article_id == 100
    assert cluster.title == "Test Event"
    assert cluster.first_published_at == published_at
    assert cluster.last_published_at == published_at

    db.add.assert_called_once_with(cluster)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(cluster)


@pytest.mark.asyncio
async def test_upsert_membership_inserts_new(
    monkeypatch,
):
    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        event_cluster_persistence_service,
        "get_event_cluster_membership",
        AsyncMock(return_value=None),
    )

    membership = await (
        event_cluster_persistence_service
        .upsert_event_cluster_membership(
            db,
            cluster_id=5,
            article_id=101,
            company_id=2,
            similarity=0.91,
        )
    )

    assert isinstance(
        membership,
        EventClusterMembership,
    )

    assert membership.cluster_id == 5
    assert membership.article_id == 101
    assert membership.company_id == 2
    assert membership.similarity == 0.91

    db.add.assert_called_once_with(membership)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        membership
    )


@pytest.mark.asyncio
async def test_upsert_membership_updates_existing(
    monkeypatch,
):
    existing = EventClusterMembership(
        cluster_id=5,
        article_id=101,
        company_id=2,
        similarity=0.80,
    )

    db = AsyncMock()
    db.add = Mock()

    monkeypatch.setattr(
        event_cluster_persistence_service,
        "get_event_cluster_membership",
        AsyncMock(
            return_value=existing
        ),
    )

    membership = await (
        event_cluster_persistence_service
        .upsert_event_cluster_membership(
            db,
            cluster_id=8,
            article_id=101,
            company_id=2,
            similarity=0.94,
        )
    )

    assert membership is existing
    assert existing.cluster_id == 8
    assert existing.similarity == 0.94

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(
        existing
    )

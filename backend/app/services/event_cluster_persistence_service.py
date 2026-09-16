from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_cluster import (
    EventCluster,
    EventClusterMembership,
)


async def get_event_cluster_membership(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
) -> EventClusterMembership | None:
    result = await db.execute(
        select(EventClusterMembership).where(
            EventClusterMembership.article_id
            == article_id,
            EventClusterMembership.company_id
            == company_id,
        )
    )

    return result.scalar_one_or_none()


async def create_event_cluster(
    db: AsyncSession,
    *,
    company_id: int,
    representative_article_id: int | None,
    title: str | None,
    first_published_at: datetime | None,
    last_published_at: datetime | None,
) -> EventCluster:
    cluster = EventCluster(
        company_id=company_id,
        representative_article_id=(
            representative_article_id
        ),
        title=title,
        first_published_at=first_published_at,
        last_published_at=last_published_at,
    )

    db.add(cluster)
    await db.commit()
    await db.refresh(cluster)

    return cluster


async def upsert_event_cluster_membership(
    db: AsyncSession,
    *,
    cluster_id: int,
    article_id: int,
    company_id: int,
    similarity: float | None,
) -> EventClusterMembership:
    existing = await get_event_cluster_membership(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    if existing is None:
        membership = EventClusterMembership(
            cluster_id=cluster_id,
            article_id=article_id,
            company_id=company_id,
            similarity=similarity,
        )

        db.add(membership)
    else:
        membership = existing
        membership.cluster_id = cluster_id
        membership.similarity = similarity

    await db.commit()
    await db.refresh(membership)

    return membership


async def get_event_cluster(
    db: AsyncSession,
    *,
    cluster_id: int,
) -> EventCluster | None:
    result = await db.execute(
        select(EventCluster).where(
            EventCluster.id == cluster_id
        )
    )

    return result.scalar_one_or_none()


async def update_event_cluster_time_bounds(
    db: AsyncSession,
    *,
    cluster_id: int,
    article_time: datetime,
) -> EventCluster | None:
    cluster = await get_event_cluster(
        db,
        cluster_id=cluster_id,
    )

    if cluster is None:
        return None

    if (
        cluster.first_published_at is None
        or article_time
        < cluster.first_published_at
    ):
        cluster.first_published_at = article_time

    if (
        cluster.last_published_at is None
        or article_time
        > cluster.last_published_at
    ):
        cluster.last_published_at = article_time

    await db.commit()
    await db.refresh(cluster)

    return cluster

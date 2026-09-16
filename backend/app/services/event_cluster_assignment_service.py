from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.article_service import get_article
from app.services.event_cluster_candidate_service import (
    find_event_cluster_candidates,
)
from app.services.event_cluster_persistence_service import (
    create_event_cluster,
    get_event_cluster_membership,
    update_event_cluster_time_bounds,
    upsert_event_cluster_membership,
)


@dataclass(frozen=True)
class EventClusterAssignmentResult:
    article_id: int
    company_id: int
    cluster_id: int
    created_new_cluster: bool
    similarity: float | None


async def assign_article_to_event_cluster(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
    minimum_similarity: float = 0.80,
    time_window_hours: int = 48,
) -> EventClusterAssignmentResult | None:
    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        return None

    existing_membership = (
        await get_event_cluster_membership(
            db,
            article_id=article_id,
            company_id=company_id,
        )
    )

    if existing_membership is not None:
        return EventClusterAssignmentResult(
            article_id=article_id,
            company_id=company_id,
            cluster_id=existing_membership.cluster_id,
            created_new_cluster=False,
            similarity=existing_membership.similarity,
        )

    candidates = await find_event_cluster_candidates(
        db,
        article_id=article_id,
        company_id=company_id,
        minimum_similarity=minimum_similarity,
        time_window_hours=time_window_hours,
    )

    if candidates:
        best_candidate = max(
            candidates,
            key=lambda item: item.similarity,
        )

        membership = (
            await upsert_event_cluster_membership(
                db,
                cluster_id=best_candidate.cluster_id,
                article_id=article_id,
                company_id=company_id,
                similarity=best_candidate.similarity,
            )
        )

        article_time = (
            article.published_at
            or article.collected_at
        )

        await update_event_cluster_time_bounds(
            db,
            cluster_id=membership.cluster_id,
            article_time=article_time,
        )

        return EventClusterAssignmentResult(
            article_id=article_id,
            company_id=company_id,
            cluster_id=membership.cluster_id,
            created_new_cluster=False,
            similarity=membership.similarity,
        )

    article_time = (
        article.published_at
        or article.collected_at
    )

    cluster = await create_event_cluster(
        db,
        company_id=company_id,
        representative_article_id=article_id,
        title=article.title,
        first_published_at=article_time,
        last_published_at=article_time,
    )

    membership = await upsert_event_cluster_membership(
        db,
        cluster_id=cluster.id,
        article_id=article_id,
        company_id=company_id,
        similarity=1.0,
    )

    return EventClusterAssignmentResult(
        article_id=article_id,
        company_id=company_id,
        cluster_id=membership.cluster_id,
        created_new_cluster=True,
        similarity=membership.similarity,
    )

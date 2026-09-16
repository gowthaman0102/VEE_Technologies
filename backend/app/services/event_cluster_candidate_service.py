from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.event_cluster import (
    EventClusterMembership,
)
from app.services.article_service import get_article


@dataclass(frozen=True)
class EventClusterCandidate:
    cluster_id: int
    article_id: int
    similarity: float


async def find_event_cluster_candidates(
    db: AsyncSession,
    *,
    article_id: int,
    company_id: int,
    minimum_similarity: float,
    time_window_hours: int,
    limit: int = 10,
) -> list[EventClusterCandidate]:
    if not -1.0 <= minimum_similarity <= 1.0:
        raise ValueError(
            "Minimum similarity must be between -1 and 1."
        )

    if time_window_hours < 1:
        raise ValueError(
            "Time window must be at least 1 hour."
        )

    if limit < 1:
        raise ValueError(
            "Candidate limit must be at least 1."
        )

    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        return []

    if (
        article.embedding_status != "success"
        or article.embedding is None
    ):
        return []

    article_time = (
        article.published_at
        or article.collected_at
    )

    start_time = article_time - timedelta(
        hours=time_window_hours
    )

    end_time = article_time + timedelta(
        hours=time_window_hours
    )

    candidate_time = func.coalesce(
        Article.published_at,
        Article.collected_at,
    )

    distance_expression = (
        Article.embedding.cosine_distance(
            article.embedding
        )
    )

    statement = (
        select(
            EventClusterMembership.cluster_id,
            Article.id.label("article_id"),
            distance_expression.label("distance"),
        )
        .join(
            EventClusterMembership,
            EventClusterMembership.article_id
            == Article.id,
        )
        .where(
            EventClusterMembership.company_id
            == company_id,
            Article.id != article_id,
            Article.embedding_status == "success",
            Article.embedding.is_not(None),
            candidate_time >= start_time,
            candidate_time <= end_time,
        )
        .order_by(
            distance_expression.asc(),
            Article.id.asc(),
        )
        .limit(limit)
    )

    result = await db.execute(statement)

    candidates: list[EventClusterCandidate] = []

    for row in result.all():
        similarity = 1.0 - float(row.distance)

        if similarity < minimum_similarity:
            continue

        candidates.append(
            EventClusterCandidate(
                cluster_id=row.cluster_id,
                article_id=row.article_id,
                similarity=similarity,
            )
        )

    return candidates

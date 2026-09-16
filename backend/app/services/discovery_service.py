from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.event_cluster import EventCluster, EventClusterMembership


async def keyword_search(
    db: AsyncSession,
    *,
    query: str,
    limit: int = 50,
) -> list[Article]:
    normalized = query.strip()
    if not normalized:
        raise ValueError("query must not be empty")
    pattern = f"%{normalized}%"
    stmt = (
        select(Article)
        .where(
            or_(
                Article.title.ilike(pattern),
                Article.description.ilike(pattern),
                Article.cleaned_content.ilike(pattern),
            )
        )
        .order_by(Article.published_at.desc().nullslast(), Article.id.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_event_clusters(
    db: AsyncSession,
    *,
    company_id: int | None = None,
    limit: int = 50,
) -> list[dict]:
    stmt = (
        select(
            EventCluster,
            func.count(EventClusterMembership.article_id).label("article_count"),
        )
        .outerjoin(
            EventClusterMembership,
            EventClusterMembership.cluster_id == EventCluster.id,
        )
        .group_by(EventCluster.id)
        .order_by(EventCluster.last_published_at.desc().nullslast(), EventCluster.id.desc())
        .limit(limit)
    )
    if company_id is not None:
        stmt = stmt.where(EventCluster.company_id == company_id)
    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": cluster.id,
            "company_id": cluster.company_id,
            "title": cluster.title,
            "representative_article_id": cluster.representative_article_id,
            "first_published_at": cluster.first_published_at,
            "last_published_at": cluster.last_published_at,
            "article_count": int(article_count),
        }
        for cluster, article_count in rows
    ]

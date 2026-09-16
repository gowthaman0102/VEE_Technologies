from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.discovery import (
    EventClusterItem,
    EventClusterResponse,
    KeywordSearchResponse,
    KeywordSearchResult,
)
from app.services.discovery_service import keyword_search, list_event_clusters

router = APIRouter(tags=["Discovery"])


@router.get("/search/keyword", response_model=KeywordSearchResponse)
async def search_keyword(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> KeywordSearchResponse:
    articles = await keyword_search(db, query=q, limit=limit)
    return KeywordSearchResponse(
        query=q.strip(),
        count=len(articles),
        results=[
            KeywordSearchResult(
                article_id=article.id,
                title=article.title,
                source_name=article.source_name,
                url=article.url,
                published_at=article.published_at,
            )
            for article in articles
        ],
    )


@router.get("/event-clusters", response_model=EventClusterResponse)
async def read_event_clusters(
    company_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> EventClusterResponse:
    items = await list_event_clusters(db, company_id=company_id, limit=limit)
    return EventClusterResponse(
        count=len(items),
        items=[EventClusterItem(**item) for item in items],
    )

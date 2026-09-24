from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.discovery import (
    KeywordSearchResponse,
    KeywordSearchResult,
)
from app.schemas.search_filters import SearchFilters
from app.services.active_company_profile_service import (
    get_active_company_profile,
)
from app.services.discovery_service import (
    keyword_search,
)

router = APIRouter(tags=["Discovery"])


@router.get("/search/keyword", response_model=KeywordSearchResponse)
async def search_keyword(
    q: str = Query(..., min_length=1, max_length=500),
    company_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=5000),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    source_name: str | None = Query(default=None, max_length=200),
    sentiment: str | None = Query(default=None, max_length=20),
    risk_level: str | None = Query(default=None, max_length=20),
    business_impact: str | None = Query(default=None, max_length=30),
    event_type: str | None = Query(default=None, max_length=50),
    event_cluster_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> KeywordSearchResponse:
    if company_id is None:
        profile = await get_active_company_profile(db)

        if profile is None:
            raise HTTPException(
                status_code=404,
                detail="No active company configured.",
            )

        company_id = profile.company_id

    try:
        filters = SearchFilters(
            start=start,
            end=end,
            source_name=source_name,
            sentiment=sentiment,
            risk_level=risk_level,
            business_impact=business_impact,
            event_type=event_type,
            event_cluster_id=event_cluster_id,
        )
    except ValidationError as exc:
        raise RequestValidationError(
            exc.errors(),
        ) from exc

    articles = await keyword_search(
        db,
        query=q,
        company_id=company_id,
        limit=limit,
        filters=filters,
    )
    return KeywordSearchResponse(
        query=q.strip(),
        count=len(articles),
        results=[
            KeywordSearchResult(
                article_id=article.article_id,
                title=article.title,
                publisher_name=article.publisher_name,
                source_name=article.source_name,
                url=article.url,
                published_at=article.published_at,
                collected_at=article.collected_at,
                event_type=article.event_type,
                sentiment=article.sentiment,
                risk_level=article.risk_level,
                risk_score=article.risk_score,
                business_impact=article.business_impact,
                event_cluster_id=article.event_cluster_id,
            )
            for article in articles
        ],
    )

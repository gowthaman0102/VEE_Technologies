from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.search_filters import SearchFilters
from app.schemas.semantic_search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultResponse,
)
from app.services.active_company_profile_service import (
    get_active_company_profile,
)
from app.services.semantic_search_service import (
    semantic_search,
)


router = APIRouter(
    prefix="/semantic-search",
    tags=["Semantic Search"],
)


@router.post(
    "",
    response_model=SemanticSearchResponse,
)
async def search_articles(
    request: SemanticSearchRequest,
    company_id: int | None = Query(default=None, ge=1),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    source_name: str | None = Query(
        default=None,
        max_length=200,
    ),
    sentiment: str | None = Query(
        default=None,
        max_length=20,
    ),
    risk_level: str | None = Query(
        default=None,
        max_length=20,
    ),
    business_impact: str | None = Query(
        default=None,
        max_length=30,
    ),
    event_type: str | None = Query(
        default=None,
        max_length=50,
    ),
    event_cluster_id: int | None = Query(
        default=None,
        ge=1,
    ),
    db: AsyncSession = Depends(get_db),
) -> SemanticSearchResponse:
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

    results = await semantic_search(
        db,
        request.query,
        limit=request.limit,
        minimum_similarity=(
            request.minimum_similarity
        ),
        company_id=company_id,
        filters=filters,
    )

    return SemanticSearchResponse(
        query=request.query.strip(),
        count=len(results),
        results=[
            SemanticSearchResultResponse(
                article_id=item.article_id,
                title=item.title,
                source_name=item.source_name,
                url=item.url,
                published_at=item.published_at,
                distance=item.distance,
                similarity=item.similarity,
                event_type=item.event_type,
                sentiment=item.sentiment,
                risk_level=item.risk_level,
                risk_score=item.risk_score,
                business_impact=item.business_impact,
                event_cluster_id=item.event_cluster_id,
            )
            for item in results
        ],
    )

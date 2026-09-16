from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.active_company_profile_service import (
    get_active_company_profile,
)
from app.schemas.semantic_search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultResponse,
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
    db: AsyncSession = Depends(get_db),
) -> SemanticSearchResponse:
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id

    results = await semantic_search(
        db,
        request.query,
        limit=request.limit,
        minimum_similarity=(
            request.minimum_similarity
        ),
        company_id=company_id,
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
            )
            for item in results
        ],
    )

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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
    db: AsyncSession = Depends(get_db),
) -> SemanticSearchResponse:
    results = await semantic_search(
        db,
        request.query,
        limit=request.limit,
        minimum_similarity=(
            request.minimum_similarity
        ),
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

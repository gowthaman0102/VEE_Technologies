from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.article import ArticleResponse
from app.services.article_service import (
    get_article,
    list_articles,
)


router = APIRouter(
    prefix="/articles",
    tags=["Articles"],
)


@router.get(
    "",
    response_model=list[ArticleResponse],
)
async def get_articles(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: AsyncSession = Depends(get_db),
) -> list[ArticleResponse]:
    articles = await list_articles(
        db,
        limit=limit,
    )

    return articles


@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
)
async def get_article_by_id(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    article = await get_article(
        db,
        article_id,
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    return article

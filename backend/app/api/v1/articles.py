from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.article_sentiment import ArticleSentiment
from app.schemas.article import ArticleResponse
from app.services.active_company_profile_service import (
    get_active_company_profile,
)
from app.services.article_service import (
    get_article,
    list_articles,
)
from app.utils.article_metadata import publisher_name, resolve_publisher_url


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

    return [
        ArticleResponse(
            **article.__dict__,
            publisher_name=publisher_name(
                article.source_name,
                article.title,
                article.url,
                article.canonical_url,
            ),
            publisher_url=resolve_publisher_url(
                article.url,
                article.canonical_url,
            ),
        )
        for article in articles
    ]


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

    # Fetch sentiment for the active company (optional enrichment)
    sentiment_label: str | None = None

    profile = await get_active_company_profile(db)

    if profile is not None:
        row = await db.scalar(
            select(ArticleSentiment.label).where(
                ArticleSentiment.article_id == article_id,
                ArticleSentiment.company_id == profile.company_id,
            )
        )
        sentiment_label = row

    return ArticleResponse(
        **article.__dict__,
        publisher_name=publisher_name(
            article.source_name,
            article.title,
            article.url,
            article.canonical_url,
        ),
        publisher_url=resolve_publisher_url(
            article.url,
            article.canonical_url,
        ),
        sentiment=sentiment_label,
    )

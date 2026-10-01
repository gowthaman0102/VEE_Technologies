from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.company import Company
from app.models.risk_assessment import RiskAssessment
from app.schemas.dashboard import DashboardArticleItem
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    ArticleTrendResponse,
    BusinessImpactResponse,
    CompetitorAnalyticsResponse,
    EventAnalyticsResponse,
    RiskTrendResponse,
    SentimentTrendResponse,
    SourceAnalyticsResponse,
)
from app.services.active_company_profile_service import get_active_company_profile
from app.services.analytics_service import (
    get_article_count,
    get_period_comparison,
    get_article_volume_over_time,
    get_business_impact_distribution,
    get_business_impact_article_query,
    get_competitor_summary,
    get_event_summary,
    get_risk_summary,
    get_sentiment_distribution,
    get_source_summary,
    validate_time_window,
)
from app.utils.article_metadata import publisher_name


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def read_analytics_overview(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id

    if start is None or end is None:
        raise HTTPException(status_code=400, detail="start and end are required")

    start, end = validate_time_window(start, end)

    sentiment = await get_sentiment_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    risk = await get_risk_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    businesses = await get_business_impact_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    competitors = await get_competitor_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    events = await get_event_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    total_articles = await get_article_count(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    comparison = await get_period_comparison(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    
    from app.services.analytics_service import get_publisher_country_distribution
    country_distribution = await get_publisher_country_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )

    return AnalyticsOverviewResponse(
        company_id=company_id,
        start=start,
        end=end,
        total_articles=total_articles,
        total_events=events["total_events"],
        sentiment={
            key: sentiment.get("summary", sentiment).get(key, sentiment.get(key, 0))
            for key in ("positive", "neutral", "negative")
        },
        risk={
            key: risk.get("summary", risk).get(key, risk.get(key, 0))
            for key in (
                "average_risk_score",
                "highest_risk_score",
                "high_risk_count",
                "medium_risk_count",
                "low_risk_count",
            )
        },
        business_impact=businesses.get("items", businesses),
        competitors=competitors.get("competitors", []),
        comparison=comparison,
        publisher_country_distribution=country_distribution["distribution"],
    )


@router.get("/articles/trend", response_model=ArticleTrendResponse)
async def read_article_trend(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    bucket: str = Query("day", pattern="^(hour|day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id
    start, end = validate_time_window(start, end)
    points = await get_article_volume_over_time(
        db,
        company_id=company_id,
        start=start,
        end=end,
        bucket=bucket,
    )
    return ArticleTrendResponse(
        company_id=company_id,
        bucket=bucket,
        points=points,
    )


@router.get("/sentiment/trend", response_model=SentimentTrendResponse)
async def read_sentiment_trend(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id
    start, end = validate_time_window(start, end)
    data = await get_sentiment_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    summary = data.get("summary", {"positive": data.get("positive", 0), "neutral": data.get("neutral", 0), "negative": data.get("negative", 0)})
    return SentimentTrendResponse(
        company_id=company_id,
        summary=summary,
        positive=summary.get("positive", 0),
        neutral=summary.get("neutral", 0),
        negative=summary.get("negative", 0),
        series=data.get("series", []),
    )


@router.get("/risk/trend", response_model=RiskTrendResponse)
async def read_risk_trend(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id
    start, end = validate_time_window(start, end)
    data = await get_risk_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    summary = data.get("summary", {
        "average_risk_score": data.get("average_risk_score", 0.0),
        "highest_risk_score": data.get("highest_risk_score", 0.0),
        "high_risk_count": data.get("high_risk_count", 0),
        "medium_risk_count": data.get("medium_risk_count", 0),
        "low_risk_count": data.get("low_risk_count", 0),
    })
    return RiskTrendResponse(
        company_id=company_id,
        summary=summary,
        average_risk_score=summary.get("average_risk_score", 0.0),
        highest_risk_score=summary.get("highest_risk_score", 0.0),
        high_risk_count=summary.get("high_risk_count", 0),
        medium_risk_count=summary.get("medium_risk_count", 0),
        low_risk_count=summary.get("low_risk_count", 0),
        series=data.get("series", []),
    )


@router.get("/business-impact", response_model=BusinessImpactResponse)
async def read_business_impact(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id
    start, end = validate_time_window(start, end)
    data = await get_business_impact_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    return BusinessImpactResponse(
        company_id=company_id,
        items=data.get("items", {}),
        primary_distribution=data.get(
            "primary_distribution",
            data.get("items", {}),
        ),
        category_distribution=data.get(
            "category_distribution",
            {},
        ),
        series=data.get("series", []),
        category_series=data.get(
            "category_series",
            [],
        ),
    )


@router.get("/business-impact/articles")
async def read_business_impact_articles(
    response: Response,
    company_id: int = Query(..., ge=1),
    category: str = Query(..., min_length=1, max_length=50),
    start: datetime = Query(...),
    end: datetime = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    if await db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    start, end = validate_time_window(start, end)

    membership_query = get_business_impact_article_query(
        company_id,
        category,
        start,
        end,
    )
    total = await db.scalar(
        select(func.count()).select_from(
            membership_query.order_by(None).subquery()
        )
    )
    statement = (
        membership_query
        .outerjoin(
            ArticleTriage,
            (ArticleTriage.article_id == Article.id)
            & (ArticleTriage.company_id == company_id),
        )
        .outerjoin(
            ArticleSentiment,
            (ArticleSentiment.article_id == Article.id)
            & (ArticleSentiment.company_id == company_id),
        )
        .outerjoin(
            RiskAssessment,
            (RiskAssessment.article_id == Article.id)
            & (RiskAssessment.company_id == company_id),
        )
        .add_columns(
            ArticleTriage.event_type,
            ArticleSentiment.label,
            RiskAssessment.risk_level,
            RiskAssessment.risk_score,
            ArticleBusinessImpact.primary_category,
        )
        .order_by(
            func.coalesce(Article.published_at, Article.collected_at).desc(),
            Article.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(statement)).all()
    items = []
    for row in rows:
        article, event_type, sentiment, risk_level, risk_score, impact = row
        items.append(
            DashboardArticleItem(
                article_id=article.id,
                title=article.title,
                source_name=article.source_name,
                url=article.url,
                published_at=article.published_at,
                publisher_name=publisher_name(
                    article.source_name,
                    article.title,
                    article.url,
                ),
                collected_at=article.collected_at,
                event_type=event_type,
                sentiment=sentiment,
                risk_level=risk_level,
                risk_score=risk_score,
                business_impact=impact,
            )
        )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return {"total": total or 0, "items": items}


@router.get("/events", response_model=EventAnalyticsResponse)
async def read_event_analytics(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id
    start, end = validate_time_window(start, end)
    data = await get_event_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    return EventAnalyticsResponse(
        company_id=company_id,
        total_events=data["total_events"],
        largest_events=data["largest_events"],
    )


@router.get("/sources", response_model=SourceAnalyticsResponse)
async def read_source_analytics(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id
    start, end = validate_time_window(start, end)
    data = await get_source_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    return SourceAnalyticsResponse(
        company_id=company_id,
        sources=data["sources"],
    )


@router.get("/competitors", response_model=CompetitorAnalyticsResponse)
async def read_competitor_analytics(
    company_id: int | None = Query(default=None, ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if company_id is None:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise HTTPException(status_code=404, detail="No active company configured.")
        company_id = profile.company_id
    start, end = validate_time_window(start, end)
    data = await get_competitor_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    return CompetitorAnalyticsResponse(
        company_id=company_id,
        competitors=data.get("competitors", []),
    )


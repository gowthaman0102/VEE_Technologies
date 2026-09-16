from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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
    get_competitor_summary,
    get_event_summary,
    get_risk_summary,
    get_sentiment_distribution,
    get_source_summary,
    validate_time_window,
)


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

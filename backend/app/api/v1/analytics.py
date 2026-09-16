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
from app.services.analytics_service import (
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
    company_id: int = Query(..., ge=1),
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
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

    return AnalyticsOverviewResponse(
        company_id=company_id,
        start=start,
        end=end,
        total_articles=0,
        total_events=events["total_events"],
        sentiment=sentiment,
        risk=risk,
        business_impact=businesses,
        competitors=competitors.get("competitors", []),
    )


@router.get("/articles/trend", response_model=ArticleTrendResponse)
async def read_article_trend(
    company_id: int = Query(..., ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    bucket: str = Query("day", pattern="^(hour|day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
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
    company_id: int = Query(..., ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    start, end = validate_time_window(start, end)
    data = await get_sentiment_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    return SentimentTrendResponse(
        company_id=company_id,
        **data,
    )


@router.get("/risk/trend", response_model=RiskTrendResponse)
async def read_risk_trend(
    company_id: int = Query(..., ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    start, end = validate_time_window(start, end)
    data = await get_risk_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    return RiskTrendResponse(
        company_id=company_id,
        **data,
    )


@router.get("/business-impact", response_model=BusinessImpactResponse)
async def read_business_impact(
    company_id: int = Query(..., ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    start, end = validate_time_window(start, end)
    data = await get_business_impact_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    return BusinessImpactResponse(
        company_id=company_id,
        items=data,
    )


@router.get("/events", response_model=EventAnalyticsResponse)
async def read_event_analytics(
    company_id: int = Query(..., ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
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
    company_id: int = Query(..., ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
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
    company_id: int = Query(..., ge=1),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
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

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.dashboard import (
    DashboardCompaniesResponse,
    DashboardArticleResponse,
    DashboardIntelligenceResponse,
    DashboardOverviewResponse,
    DashboardRiskAnalyticsResponse,
    RiskDrilldownResponse,
)
from app.services.dashboard_service import (
    get_dashboard_companies,
    get_dashboard_articles,
    get_dashboard_intelligence,
    get_dashboard_overview,
    get_dashboard_risk_analytics,
    get_dashboard_risk_analytics_drilldown,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
)
async def read_dashboard_overview(
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_overview(
        db,
    )


@router.get(
    "/intelligence",
    response_model=DashboardIntelligenceResponse,
)
async def read_dashboard_intelligence(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_intelligence(
        db,
        limit=limit,
    )


@router.get(
    "/articles",
    response_model=DashboardArticleResponse,
)
async def read_dashboard_articles(
    metric: Literal["total", "processed", "high-risk", "critical-risk"] = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_articles(db, metric=metric)


@router.get(
    "/risk-analytics",
    response_model=DashboardRiskAnalyticsResponse,
)
async def read_dashboard_risk_analytics(
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_risk_analytics(
        db,
    )


@router.get(
    "/companies",
    response_model=DashboardCompaniesResponse,
)
async def read_dashboard_companies(
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_companies(
        db,
    )


@router.get(
    "/risk-analytics/drilldown",
    response_model=RiskDrilldownResponse,
)
async def read_dashboard_risk_analytics_drilldown(
    metric: str = Query(...),
    value: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_risk_analytics_drilldown(
        db,
        metric=metric,
        value=value,
        page=page,
        page_size=page_size,
        search=search,
    )

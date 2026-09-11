from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.dashboard import (
    DashboardAlertsResponse,
    DashboardCompaniesResponse,
    DashboardIntelligenceResponse,
    DashboardOverviewResponse,
    DashboardRiskAnalyticsResponse,
)
from app.services.dashboard_service import (
    get_dashboard_alerts,
    get_dashboard_companies,
    get_dashboard_intelligence,
    get_dashboard_overview,
    get_dashboard_risk_analytics,
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
    "/alerts",
    response_model=DashboardAlertsResponse,
)
async def read_dashboard_alerts(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_alerts(
        db,
        limit=limit,
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

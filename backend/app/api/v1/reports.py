from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.reports import (
    ReportExportResponse,
    ReportRequest,
    ReportSummaryResponse,
)
from app.services.report_service import build_company_report, export_report_csv

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=ReportSummaryResponse)
async def get_report_summary(
    company_id: int = Query(..., gt=0),
    start_date: str = Query(..., min_length=1),
    end_date: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
) -> ReportSummaryResponse:
    try:
        report = await build_company_report(
            db,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return ReportSummaryResponse(**report)


@router.post("/export", response_model=ReportExportResponse)
async def export_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> ReportExportResponse:
    try:
        report = await build_company_report(
            db,
            company_id=payload.company_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    csv_content = export_report_csv(report)
    return ReportExportResponse(
        company_id=payload.company_id,
        format="csv",
        filename=f"company-{payload.company_id}-report.csv",
        content_type="text/csv",
        rows=[
            {"metric": row[0], "value": row[1]}
            for row in [
                ["company_id", str(report["company_id"])],
                ["start_date", report["start_date"]],
                ["end_date", report["end_date"]],
                ["total_articles", str(report["total_articles"])],
                ["total_events", str(report["total_events"])],
                ["high_risk_count", str(report["high_risk_count"])],
                ["medium_risk_count", str(report["medium_risk_count"])],
                ["low_risk_count", str(report["low_risk_count"])],
            ]
        ],
    )

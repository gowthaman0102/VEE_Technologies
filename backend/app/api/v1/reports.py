from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.generated_report import GeneratedReport
from app.schemas.reports import (
    ReportHistoryItem,
    ReportHistoryResponse,
    ReportRequest,
    ReportSummaryResponse,
)
from app.services.report_service import (
    build_company_report,
    persist_generated_report,
    render_report,
)

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
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReportSummaryResponse(**report)


@router.post("/export")
async def export_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        start_date, end_date = _resolve_period(payload)
        report = await build_company_report(
            db,
            company_id=payload.company_id,
            start_date=start_date,
            end_date=end_date,
        )
        content = render_report(report, payload.format)
        record = await persist_generated_report(
            db,
            report_data=report,
            file_format=payload.format,
            content=content,
            report_type=payload.report_type,
        )
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Report already exists for this period and format.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(
        content=record.content,
        media_type=record.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{record.filename}"',
            "X-Report-Id": str(record.id),
        },
    )


def _resolve_period(payload: ReportRequest) -> tuple[datetime, datetime]:
    end = payload.end_date or datetime.now(timezone.utc)
    if payload.report_type == "daily":
        start = end - timedelta(days=1)
    elif payload.report_type == "weekly":
        start = end - timedelta(days=7)
    elif payload.report_type == "monthly":
        start = end - timedelta(days=30)
    else:
        if payload.start_date is None:
            raise HTTPException(status_code=422, detail="start_date is required for custom reports.")
        start = payload.start_date
    return start, end


@router.post("/generate")
async def generate_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    response = await export_report(payload, db)
    return {
        "status": "success",
        "filename": response.headers.get("content-disposition"),
        "report_id": response.headers.get("x-report-id"),
    }


@router.get("/history", response_model=ReportHistoryResponse)
async def report_history(
    company_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ReportHistoryResponse:
    stmt = select(GeneratedReport).order_by(GeneratedReport.created_at.desc()).limit(limit)
    if company_id is not None:
        stmt = stmt.where(GeneratedReport.company_id == company_id)
    records = list((await db.execute(stmt)).scalars().all())
    return ReportHistoryResponse(
        count=len(records),
        items=[ReportHistoryItem.model_validate(record, from_attributes=True) for record in records],
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    record = await db.get(GeneratedReport, report_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return Response(
        content=record.content,
        media_type=record.content_type,
        headers={"Content-Disposition": f'attachment; filename="{record.filename}"'},
    )

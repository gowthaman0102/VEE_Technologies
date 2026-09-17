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
    generate_report_record,
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
        start_date, end_date = _resolve_period(
            payload
        )

        record = await generate_report_record(
            db,
            company_id=payload.company_id,
            report_type=payload.report_type,
            file_format=payload.format,
            period_start=start_date,
            period_end=end_date,
        )

    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Report already exists for "
                "this period and format."
            ),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if (
        record.status != "success"
        or record.content is None
        or record.filename is None
        or record.content_type is None
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Report is not available "
                "for download."
            ),
        )

    return Response(
        content=record.content,
        media_type=record.content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="'
                f'{record.filename}"'
            ),
            "X-Report-Id": str(record.id),
        },
    )


def _as_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def _resolve_period(
    payload: ReportRequest,
) -> tuple[datetime, datetime]:
    reference = _as_utc(
        payload.end_date
        or datetime.now(timezone.utc)
    )

    day_start = reference.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if payload.report_type == "daily":
        end = day_start
        start = end - timedelta(
            days=1
        )
        return start, end

    if payload.report_type == "weekly":
        end = day_start - timedelta(
            days=day_start.weekday()
        )
        start = end - timedelta(
            days=7
        )
        return start, end

    if payload.report_type == "monthly":
        end = day_start.replace(
            day=1
        )

        if end.month == 1:
            start = end.replace(
                year=end.year - 1,
                month=12,
            )
        else:
            start = end.replace(
                month=end.month - 1
            )

        return start, end

    if payload.start_date is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "start_date is required "
                "for custom reports."
            ),
        )

    start = _as_utc(
        payload.start_date
    )
    end = reference

    return start, end


@router.post("/generate")
async def generate_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        start_date, end_date = _resolve_period(
            payload
        )

        record = await generate_report_record(
            db,
            company_id=payload.company_id,
            report_type=payload.report_type,
            file_format=payload.format,
            period_start=start_date,
            period_end=end_date,
        )

    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Report already exists for "
                "this period and format."
            ),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "report_id": record.id,
        "status": record.status,
        "filename": record.filename,
        "content_type": record.content_type,
        "error": record.error,
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
    record = await db.get(
        GeneratedReport,
        report_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    if record.status != "success":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report is not ready for download.",
        )

    if (
        record.content is None
        or record.filename is None
        or record.content_type is None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Report file is incomplete "
                "and cannot be downloaded."
            ),
        )

    return Response(
        content=record.content,
        media_type=record.content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="'
                f'{record.filename}"'
            ),
        },
    )

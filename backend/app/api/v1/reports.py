from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.article import Article
from app.models.generated_report import GeneratedReport
from app.schemas.reports import (
    ReportBatchHistoryItem,
    ReportHistoryItem,
    ReportHistoryResponse,
    ReportRequest,
    ReportSummaryResponse,
)
from app.services.report_service import (
    build_company_report,
    generate_report_batch,
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
        snapshot_at = datetime.now(timezone.utc)
        report = await build_company_report(
            db,
            company_id=company_id,
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date),
            snapshot_at=snapshot_at,
            time_mode="media",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReportSummaryResponse(**report)


@router.post("/export")
async def export_report(
    payload: ReportRequest,
    file_format: str = Query(default="pdf", pattern="^(pdf|xlsx|csv)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        start_date, end_date = await _resolve_period_for_request(
            payload, db
        )
        records = await generate_report_batch(
            db,
            company_id=payload.company_id,
            report_type=payload.report_type,
            period_start=start_date,
            period_end=end_date,
            time_mode=payload.time_mode,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    record = next(
        (r for r in records if r.file_format == file_format), None
    )
    if record is None or record.status != "success" or record.content is None:
        raise HTTPException(
            status_code=409,
            detail="Report is not available for download.",
        )

    return Response(
        content=record.content,
        media_type=record.content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{record.filename}"'
            ),
            "X-Report-Id": str(record.id),
            "X-Batch-Id": str(record.batch_id),
        },
    )


def _as_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _resolve_period(
    payload: ReportRequest,
) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)

    if payload.report_type == "all_history":
        raise ValueError("all_history requires database resolution")

    if payload.time_mode == "ingestion":
        if payload.report_type == "custom":
            if payload.start_date is None:
                raise HTTPException(
                    status_code=422,
                    detail="start_date is required for custom reports.",
                )
            start = _as_utc(payload.start_date)
            end = _as_utc(payload.end_date) if payload.end_date else now
            return start, end

        if payload.report_type == "daily":
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return day_start - timedelta(days=1), day_start

        if payload.report_type == "weekly":
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return day_start - timedelta(weeks=1), now

        if payload.report_type == "monthly":
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return day_start - timedelta(days=30), now

        return now - timedelta(hours=1), now

    # MEDIA mode
    reference = _as_utc(
        payload.end_date or now
    )

    day_start = reference.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    if payload.report_type == "daily":
        end = day_start
        start = end - timedelta(days=1)
        return start, end

    if payload.report_type == "weekly":
        end = day_start - timedelta(days=day_start.weekday())
        start = end - timedelta(days=7)
        return start, end

    if payload.report_type == "monthly":
        end = day_start.replace(day=1)
        if end.month == 1:
            start = end.replace(year=end.year - 1, month=12)
        else:
            start = end.replace(month=end.month - 1)
        return start, end

    if payload.start_date is None:
        raise HTTPException(
            status_code=422,
            detail="start_date is required for custom reports.",
        )

    start = _as_utc(payload.start_date)
    end = reference
    return start, end


async def _resolve_period_for_request(
    payload: ReportRequest,
    db: AsyncSession,
) -> tuple[datetime, datetime]:
    if payload.report_type != "all_history":
        return _resolve_period(payload)

    article_time = func.coalesce(
        Article.published_at,
        Article.collected_at,
    )
    result = await db.execute(
        select(func.min(article_time), func.max(article_time))
    )
    oldest, newest = result.one()
    reference = _as_utc(
        payload.end_date or datetime.now(timezone.utc)
    )
    if oldest is None or newest is None:
        return reference - timedelta(days=1), reference
    return oldest, newest + timedelta(microseconds=1)


@router.post("/generate")
async def generate_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        start_date, end_date = await _resolve_period_for_request(
            payload, db
        )
        records = await generate_report_batch(
            db,
            company_id=payload.company_id,
            report_type=payload.report_type,
            period_start=start_date,
            period_end=end_date,
            time_mode=payload.time_mode,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    batch_id = records[0].batch_id if records else None
    formats = {
        r.file_format: {
            "report_id": r.id,
            "status": r.status,
            "filename": r.filename,
            "content_type": r.content_type,
            "error": r.error,
        }
        for r in records
    }

    return {
        "batch_id": batch_id,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "formats": formats,
    }


@router.get("/history", response_model=ReportHistoryResponse)
async def report_history(
    company_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ReportHistoryResponse:
    stmt = (
        select(GeneratedReport)
        .order_by(GeneratedReport.created_at.desc())
        .limit(limit * 3)
    )
    if company_id is not None:
        stmt = stmt.where(GeneratedReport.company_id == company_id)
    records = list((await db.execute(stmt)).scalars().all())

    # Group by batch_id; records without a batch_id get their own synthetic group
    batches: dict[str, list[GeneratedReport]] = defaultdict(list)
    for r in records:
        key = r.batch_id if r.batch_id else f"solo-{r.id}"
        batches[key].append(r)

    batch_items: list[ReportBatchHistoryItem] = []
    seen_batches: set[str] = set()
    for r in records:
        key = r.batch_id if r.batch_id else f"solo-{r.id}"
        if key in seen_batches:
            continue
        seen_batches.add(key)
        batch_records = batches[key]

        primary = batch_records[0]
        formats_map = {
            br.file_format: ReportHistoryItem.model_validate(
                br, from_attributes=True
            )
            for br in batch_records
        }

        overall_status = (
            "success"
            if all(br.status == "success" for br in batch_records)
            else "failed"
            if any(br.status == "failed" for br in batch_records)
            else "processing"
        )

        batch_items.append(
            ReportBatchHistoryItem(
                batch_id=key,
                company_id=primary.company_id,
                report_type=primary.report_type,
                period_start=primary.period_start,
                period_end=primary.period_end,
                status=overall_status,
                generated_at=primary.generated_at,
                error=primary.error,
                formats=formats_map,
            )
        )

        if len(batch_items) >= limit:
            break

    return ReportHistoryResponse(
        count=len(batch_items),
        items=batch_items,
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    record = await db.get(GeneratedReport, report_id)

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
            detail="Report file is incomplete and cannot be downloaded.",
        )

    return Response(
        content=record.content,
        media_type=record.content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{record.filename}"'
            ),
        },
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    record = await db.get(GeneratedReport, report_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    await db.delete(record)
    await db.commit()

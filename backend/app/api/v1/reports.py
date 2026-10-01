from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.article import Article
from app.models.company import Company
from app.models.generated_report import GeneratedReport
from app.schemas.reports import (
    ReportBatchHistoryItem,
    ReportHistoryItem,
    ReportHistoryResponse,
    ReportRequest,
    ReportSummaryResponse,
)
from app.services.semantic_search_service import semantic_search, SearchFilters
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
        record = await generate_report_record(db, payload, file_format)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if record.status != "success" or record.content is None:
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
            "X-Batch-Id": str(getattr(record, "batch_id", None)),
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
    reference = _as_utc(payload.end_date) if payload.end_date else now

    if payload.report_type == "all_history":
        raise ValueError("all_history requires database resolution")

    if payload.report_type == "custom":
        if payload.start_date is None:
            raise HTTPException(
                status_code=422,
                detail="start_date is required for custom reports.",
            )
        start = _as_utc(payload.start_date)
        return start, reference

    if payload.report_type == "daily":
        return reference - timedelta(days=1), reference

    if payload.report_type == "weekly":
        return reference - timedelta(days=7), reference

    if payload.report_type == "monthly":
        return reference - timedelta(days=30), reference

    return reference - timedelta(hours=1), reference


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


async def generate_report_record(
    db: AsyncSession,
    payload: ReportRequest,
    file_format: str,
) -> "GeneratedReport":
    """
    Resolve period, run search resolution if needed, generate one batch,
    return the specific-format record.  Raises HTTPException on failure.
    """
    start_date, end_date = await _resolve_period_for_request(payload, db)

    if payload.report_scope == "search_results":
        if not payload.article_ids:
            raise ValueError("article_ids are required for search_results report scope.")
        
        # We don't fetch or re-run the search here; we strictly use payload.article_ids
        # Validation of these IDs will happen downstream.

    records = await generate_report_batch(
        db,
        company_id=payload.company_id,
        report_type=payload.report_type,
        period_start=start_date,
        period_end=end_date,
        time_mode=payload.time_mode,
        report_scope=payload.report_scope,
        article_ids=payload.article_ids,
        business_impact_category=payload.business_impact_category,
        include_details=payload.include_details,
        report_template=payload.report_template,
        search_query=payload.search_query,
        search_mode=payload.search_mode,
        search_filters=payload.search_filters,
        minimum_similarity=payload.minimum_similarity,
        scope_metadata=payload.scope_metadata,
    )

    record = next((r for r in records if r.file_format == file_format), None)
    if record is None:
        raise HTTPException(status_code=500, detail="Report record not found after generation.")
    return record


@router.post("/generate")
async def generate_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        # Use pdf as the primary format; generate_report_record creates the full batch
        record = await generate_report_record(db, payload, "pdf")
    except HTTPException:
        raise
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
        "batch_id": getattr(record, "batch_id", None),
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
        key = getattr(r, "batch_id", None) or f"solo-{r.id}"
        batches[key].append(r)

    batch_items: list[ReportBatchHistoryItem] = []
    seen_batches: set[str] = set()
    for r in records:
        key = getattr(r, "batch_id", None) or f"solo-{r.id}"
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
                id=primary.id,
                company_id=primary.company_id,
                report_type=primary.report_type,
                report_template=primary.report_template,
                report_scope=primary.report_scope,
                scope_metadata=primary.scope_metadata,
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

from fastapi import UploadFile, File, Form
import uuid

@router.post("/analytics-snapshot")
async def upload_analytics_snapshot(
    company_id: int = Form(...),
    period_start: str = Form(...),
    period_end: str = Form(...),
    time_mode: str = Form("media"),
    preset: str = Form("custom"),
    snapshot: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if snapshot.content_type != "image/png":
        raise HTTPException(400, "Only PNG snapshots are allowed")

    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(404, "Company was not found")

    try:
        start_dt = datetime.fromisoformat(period_start)
        end_dt = datetime.fromisoformat(period_end)
    except ValueError as exc:
        raise HTTPException(422, "Snapshot period is invalid") from exc
    if end_dt <= start_dt:
        raise HTTPException(422, "Snapshot period end must be after start")

    content = await snapshot.read(20 * 1024 * 1024 + 1)
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "Snapshot image exceeds the 20 MB limit")
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(400, "Snapshot content is not a valid PNG image")

    captured_at = datetime.now(timezone.utc)
    batch_id = str(uuid.uuid4())
    filename = (
        f"company-{company_id}-analytics-snapshot-"
        f"{start_dt.date().isoformat()}-{end_dt.date().isoformat()}-"
        f"{captured_at:%Y%m%dT%H%M%SZ}.png"
    )

    report = GeneratedReport(
        batch_id=batch_id,
        company_id=company_id,
        report_type="custom",
        report_template="snapshot",
        report_scope="analytics_snapshot",
        time_mode=time_mode,
        period_start=start_dt,
        period_end=end_dt,
        snapshot_at=captured_at,
        scope_metadata={
            "preset": preset,
            "captured_at": captured_at.isoformat(),
            "page": "analytics",
        },
        file_format="png",
        filename=filename,
        content_type="image/png",
        content=content,
        status="success",
        generated_at=captured_at,
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return {
        "batch_id": batch_id,
        "report_id": report.id,
        "filename": report.filename,
    }


@router.post("/intelligence-export-summary")
async def generate_intelligence_export_summary(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    payload.report_scope = "intelligence_export"
    start_date, end_date = await _resolve_period_for_request(payload, db)
    records = await generate_report_batch(
        db,
        company_id=payload.company_id,
        report_type=payload.report_type,
        period_start=start_date,
        period_end=end_date,
        time_mode=payload.time_mode,
        report_scope="intelligence_export",
        article_ids=payload.article_ids,
        business_impact_category=payload.business_impact_category,
        include_details=payload.include_details,
        report_template=payload.report_template,
        search_query=payload.search_query,
        search_mode=payload.search_mode,
        search_filters=payload.search_filters,
    )
    return {
        "batch_id": records[0].batch_id if records else None,
        "status": "success"
    }

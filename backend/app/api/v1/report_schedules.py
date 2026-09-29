from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.company import Company
from app.models.report_recipient import ReportRecipient
from app.models.report_schedule import ReportSchedule
from app.schemas.report_management import (
    ReportRecipientsResponse,
    ReportRecipientsUpdate,
    ReportScheduleListResponse,
    ReportSchedulePayload,
    ReportScheduleResponse,
)
from app.services.report_email_service import report_email_delivery_configured
from app.services.report_schedule_service import calculate_next_run_at


router = APIRouter(tags=["Report scheduling and delivery"])


async def _require_company(db: AsyncSession, company_id: int) -> None:
    if await db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found.")


def _next_run(payload: ReportSchedulePayload) -> datetime:
    return calculate_next_run_at(
        report_type=payload.report_type,
        run_time_utc=payload.run_time_utc,
        day_of_week=payload.day_of_week,
        day_of_month=payload.day_of_month,
    )


@router.post(
    "/companies/{company_id}/report-schedules",
    response_model=ReportScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report_schedule(
    company_id: int,
    payload: ReportSchedulePayload,
    db: AsyncSession = Depends(get_db),
) -> ReportScheduleResponse:
    await _require_company(db, company_id)
    schedule = ReportSchedule(
        company_id=company_id,
        **payload.model_dump(),
        next_run_at=_next_run(payload),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return ReportScheduleResponse.model_validate(schedule)


@router.get(
    "/companies/{company_id}/report-schedules",
    response_model=ReportScheduleListResponse,
)
async def read_report_schedules(
    company_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReportScheduleListResponse:
    await _require_company(db, company_id)
    schedules = list((await db.execute(
        select(ReportSchedule)
        .where(ReportSchedule.company_id == company_id)
        .order_by(ReportSchedule.created_at.desc())
    )).scalars().all())
    return ReportScheduleListResponse(
        count=len(schedules),
        items=[ReportScheduleResponse.model_validate(item) for item in schedules],
    )


@router.put("/report-schedules/{schedule_id}", response_model=ReportScheduleResponse)
async def replace_report_schedule(
    schedule_id: int,
    payload: ReportSchedulePayload,
    db: AsyncSession = Depends(get_db),
) -> ReportScheduleResponse:
    schedule = await db.get(ReportSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Report schedule not found.")
    for key, value in payload.model_dump().items():
        setattr(schedule, key, value)
    schedule.next_run_at = _next_run(payload)
    schedule.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(schedule)
    return ReportScheduleResponse.model_validate(schedule)


@router.delete("/report-schedules/{schedule_id}")
async def remove_report_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    schedule = await db.get(ReportSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Report schedule not found.")
    await db.delete(schedule)
    await db.commit()
    return {"deleted": True}


@router.get(
    "/companies/{company_id}/report-recipients",
    response_model=ReportRecipientsResponse,
)
async def read_report_recipients(
    company_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReportRecipientsResponse:
    await _require_company(db, company_id)
    emails = list((await db.execute(
        select(ReportRecipient.email)
        .where(ReportRecipient.company_id == company_id)
        .order_by(ReportRecipient.email)
    )).scalars().all())
    return ReportRecipientsResponse(
        count=len(emails),
        emails=emails,
        delivery_configured=report_email_delivery_configured(),
    )


@router.put(
    "/companies/{company_id}/report-recipients",
    response_model=ReportRecipientsResponse,
)
async def replace_report_recipients(
    company_id: int,
    payload: ReportRecipientsUpdate,
    db: AsyncSession = Depends(get_db),
) -> ReportRecipientsResponse:
    await _require_company(db, company_id)
    await db.execute(delete(ReportRecipient).where(ReportRecipient.company_id == company_id))
    db.add_all(
        ReportRecipient(company_id=company_id, email=email)
        for email in payload.emails
    )
    await db.commit()
    return ReportRecipientsResponse(
        count=len(payload.emails),
        emails=payload.emails,
        delivery_configured=report_email_delivery_configured(),
    )
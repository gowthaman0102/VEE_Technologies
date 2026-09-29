import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.celery_session import CeleryAsyncSessionLocal
from app.models.company import Company
from app.models.report_schedule import ReportSchedule
from app.services.report_service import generate_report_batch
from app.services.report_schedule_service import calculate_next_run_at


logger = logging.getLogger(__name__)


def _scheduled_report_period(
    report_type: str,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    current = now or datetime.now(timezone.utc)

    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    today_start = current.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    if report_type == "daily":
        end = today_start
        start = end - timedelta(days=1)
        return start, end

    if report_type == "weekly":
        end = today_start - timedelta(days=today_start.weekday())
        start = end - timedelta(days=7)
        return start, end

    if report_type == "monthly":
        end = today_start.replace(day=1)
        if end.month == 1:
            start = end.replace(year=end.year - 1, month=12)
        else:
            start = end.replace(month=end.month - 1)
        return start, end

    raise ValueError(
        f"Unsupported scheduled report type: {report_type}"
    )


async def _generate_scheduled_reports(
    report_type: str,
) -> dict:
    start, end = _scheduled_report_period(report_type)

    generated_batch_ids = []

    async with CeleryAsyncSessionLocal() as db:
        companies = list(
            (
                await db.execute(
                    select(Company).where(Company.is_active.is_(True))
                )
            ).scalars().all()
        )
        for company in companies:
            try:
                records = await generate_report_batch(
                    db,
                    company_id=company.id,
                    report_type=report_type,
                    period_start=start,
                    period_end=end,
                    time_mode="media",
                )
                if records:
                    generated_batch_ids.append(records[0].batch_id)
            except Exception:
                continue

    return {
        "generated_batch_ids": generated_batch_ids,
        "count": len(generated_batch_ids),
    }


@celery_app.task(name="reports.generate_daily")
def generate_daily_reports_task() -> dict:
    return asyncio.run(_generate_scheduled_reports("daily"))


@celery_app.task(name="reports.generate_weekly")
def generate_weekly_reports_task() -> dict:
    return asyncio.run(_generate_scheduled_reports("weekly"))


@celery_app.task(name="reports.generate_monthly")
def generate_monthly_reports_task() -> dict:
    return asyncio.run(_generate_scheduled_reports("monthly"))


async def _run_due_report_schedules() -> dict:
    now = datetime.now(timezone.utc)
    generated_batch_ids = []
    async with CeleryAsyncSessionLocal() as db:
        due = list((await db.execute(
            select(ReportSchedule)
            .where(
                ReportSchedule.is_active.is_(True),
                ReportSchedule.next_run_at <= now,
            )
            .order_by(ReportSchedule.next_run_at)
            .with_for_update(skip_locked=True)
            .limit(100)
        )).scalars().all())

        schedules = []
        for schedule in due:
            schedules.append({
                "id": schedule.id,
                "company_id": schedule.company_id,
                "name": schedule.name,
                "report_type": schedule.report_type,
                "time_mode": schedule.time_mode,
                "report_scope": schedule.report_scope,
                "business_impact_category": schedule.business_impact_category,
                "report_template": schedule.report_template,
                "formats": list(schedule.formats),
                "custom_period_days": schedule.custom_period_days,
            })
            schedule.next_run_at = calculate_next_run_at(
                report_type=schedule.report_type,
                run_time_utc=schedule.run_time_utc,
                now=now,
                day_of_week=schedule.day_of_week or 0,
                day_of_month=schedule.day_of_month or 1,
            )
        await db.commit()

        for spec in schedules:
            try:
                if spec["report_type"] == "custom":
                    end = now
                    start = end - timedelta(days=spec["custom_period_days"])
                else:
                    start, end = _scheduled_report_period(spec["report_type"], now=now)
                records = await generate_report_batch(
                    db,
                    company_id=spec["company_id"],
                    report_type=spec["report_type"],
                    period_start=start,
                    period_end=end,
                    time_mode=spec["time_mode"],
                    report_scope=spec["report_scope"],
                    business_impact_category=spec["business_impact_category"],
                    report_template=spec["report_template"],
                    include_details=spec["report_template"] == "detailed",
                    formats=spec["formats"],
                    schedule_id=spec["id"],
                )
                schedule = await db.get(ReportSchedule, spec["id"])
                if schedule is not None:
                    schedule.last_run_at = now
                    await db.commit()
                if records:
                    generated_batch_ids.append(records[0].batch_id)
            except Exception:
                await db.rollback()
                logger.exception(
                    "Scheduled report failed for schedule %s (%s)",
                    spec["id"],
                    spec["name"],
                )

    return {"generated_batch_ids": generated_batch_ids, "count": len(generated_batch_ids)}


@celery_app.task(name="reports.run_due_schedules")
def run_due_report_schedules_task() -> dict:
    return asyncio.run(_run_due_report_schedules())

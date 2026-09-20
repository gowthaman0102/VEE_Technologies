import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.celery_session import CeleryAsyncSessionLocal
from app.models.company import Company
from app.services.report_service import generate_report_batch


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

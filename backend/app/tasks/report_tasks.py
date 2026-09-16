import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.celery_session import CeleryAsyncSessionLocal
from app.models.company import Company
from app.services.report_service import (
    build_company_report,
    persist_generated_report,
    render_report,
)


async def _generate_scheduled_reports() -> dict:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    generated = []

    async with CeleryAsyncSessionLocal() as db:
        companies = list(
            (await db.execute(select(Company).where(Company.is_active.is_(True)))).scalars().all()
        )
        for company in companies:
            report = await build_company_report(
                db,
                company_id=company.id,
                start_date=start,
                end_date=end,
            )
            content = render_report(report, "pdf")
            record = await persist_generated_report(
                db,
                report_data=report,
                file_format="pdf",
                content=content,
            )
            generated.append(record.id)

    return {"generated_report_ids": generated, "count": len(generated)}


@celery_app.task(name="reports.generate_weekly")
def generate_weekly_reports_task() -> dict:
    return asyncio.run(_generate_scheduled_reports())

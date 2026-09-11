import asyncio

from app.core.celery_app import celery_app
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.services.alert_sla_monitor_service import (
    get_overdue_alerts,
)


async def _check_alert_sla() -> dict:
    async with CeleryAsyncSessionLocal() as db:
        overdue = await get_overdue_alerts(
            db,
        )

        return {
            "overdue_count": len(overdue),
            "alerts": [
                {
                    "alert_id": item.alert_id,
                    "article_id": item.article_id,
                    "company_id": item.company_id,
                    "alert_type": item.alert_type,
                    "severity": item.severity,
                    "delivery_status": (
                        item.delivery_status
                    ),
                    "sla_due_at": (
                        item.sla_due_at.isoformat()
                    ),
                }
                for item in overdue
            ],
        }


@celery_app.task(
    name="alerts.check_sla",
)
def check_alert_sla_task() -> dict:
    return asyncio.run(
        _check_alert_sla()
    )

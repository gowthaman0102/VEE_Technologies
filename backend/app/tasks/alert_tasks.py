import asyncio

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.services.alert_delivery_service import (
    deliver_alert,
)


class AlertDeliveryRetryError(Exception):
    pass


async def _deliver_alert(
    *,
    alert_id: int,
) -> dict:
    async with CeleryAsyncSessionLocal() as db:
        alert = await deliver_alert(
            db,
            alert_id=alert_id,
        )

        result = {
            "alert_id": alert.id,
            "article_id": alert.article_id,
            "company_id": alert.company_id,
            "status": alert.delivery_status,
            "channel": alert.delivery_channel,
            "retry_count": alert.retry_count,
            "last_error": alert.last_error,
            "delivered_at": (
                alert.delivered_at.isoformat()
                if alert.delivered_at is not None
                else None
            ),
        }

        if alert.delivery_status == "failed":
            if (
                alert.last_error
                == "Slack webhook is not configured."
            ):
                return result

            raise AlertDeliveryRetryError(
                alert.last_error
                or "Alert delivery failed."
            )

        return result


@celery_app.task(
    bind=True,
    name="alerts.deliver",
    autoretry_for=(
        AlertDeliveryRetryError,
    ),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=(
        settings.alert_delivery_max_retries
    ),
)
def deliver_alert_task(
    self,
    alert_id: int,
) -> dict:
    return asyncio.run(
        _deliver_alert(
            alert_id=alert_id,
        )
    )

from datetime import datetime, timezone

from sqlalchemy import select

from app.models.alert import Alert
from app.services.slack_alert_service import (
    SlackDeliveryResult,
    send_alert_to_slack,
)


class AlertNotFoundError(ValueError):
    pass


async def deliver_alert(
    db,
    *,
    alert_id: int,
) -> Alert:
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
        )
    )

    alert = result.scalar_one_or_none()

    if alert is None:
        raise AlertNotFoundError(
            f"Alert {alert_id} not found."
        )

    alert.delivery_channel = "slack"

    delivery: SlackDeliveryResult = (
        await send_alert_to_slack(
            alert=alert,
        )
    )

    if delivery.delivered:
        alert.delivery_status = "delivered"
        alert.delivered_at = datetime.now(
            timezone.utc
        )
        alert.last_error = None

    else:
        alert.delivery_status = "failed"
        alert.retry_count += 1
        alert.last_error = delivery.error

    await db.commit()
    await db.refresh(alert)

    return alert

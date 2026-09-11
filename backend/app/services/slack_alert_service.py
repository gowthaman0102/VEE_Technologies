from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.models.alert import Alert


@dataclass(frozen=True)
class SlackDeliveryResult:
    delivered: bool
    status_code: int | None
    error: str | None


def build_slack_payload(
    *,
    alert: Alert,
) -> dict:
    return {
        "text": (
            f"*{alert.severity.upper()} ALERT*\n"
            f"*{alert.title}*\n\n"
            f"{alert.message}\n\n"
            f"Alert type: {alert.alert_type}\n"
            f"Article ID: {alert.article_id}\n"
            f"Company ID: {alert.company_id}"
        )
    }


async def send_alert_to_slack(
    *,
    alert: Alert,
) -> SlackDeliveryResult:
    webhook_url = settings.slack_webhook_url

    if not webhook_url:
        return SlackDeliveryResult(
            delivered=False,
            status_code=None,
            error="Slack webhook is not configured.",
        )

    payload = build_slack_payload(
        alert=alert,
    )

    try:
        async with httpx.AsyncClient(
            timeout=settings.alert_delivery_timeout_seconds,
        ) as client:
            response = await client.post(
                webhook_url,
                json=payload,
            )

    except httpx.HTTPError as exc:
        return SlackDeliveryResult(
            delivered=False,
            status_code=None,
            error=str(exc),
        )

    if 200 <= response.status_code < 300:
        return SlackDeliveryResult(
            delivered=True,
            status_code=response.status_code,
            error=None,
        )

    return SlackDeliveryResult(
        delivered=False,
        status_code=response.status_code,
        error=(
            f"Slack returned HTTP "
            f"{response.status_code}."
        ),
    )

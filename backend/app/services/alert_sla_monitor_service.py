from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.alert import Alert


@dataclass(frozen=True)
class OverdueAlert:
    alert_id: int
    article_id: int
    company_id: int
    alert_type: str
    severity: str
    delivery_status: str
    sla_due_at: datetime


async def get_overdue_alerts(
    db,
    *,
    now: datetime | None = None,
) -> list[OverdueAlert]:
    current_time = now or datetime.now(
        timezone.utc
    )

    if current_time.tzinfo is None:
        raise ValueError(
            "now must be timezone-aware."
        )

    result = await db.execute(
        select(Alert)
        .where(
            Alert.sla_due_at.is_not(None),
            Alert.sla_due_at < current_time,
            Alert.delivered_at.is_(None),
        )
        .order_by(
            Alert.sla_due_at.asc()
        )
    )

    alerts = result.scalars().all()

    return [
        OverdueAlert(
            alert_id=alert.id,
            article_id=alert.article_id,
            company_id=alert.company_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            delivery_status=alert.delivery_status,
            sla_due_at=alert.sla_due_at,
        )
        for alert in alerts
    ]

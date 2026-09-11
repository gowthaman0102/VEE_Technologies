from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


SLA_MINUTES: dict[str, int] = {
    "review": 60,
    "urgent": 15,
}


@dataclass(frozen=True)
class AlertSLA:
    alert_type: str
    sla_minutes: int
    created_at: datetime
    due_at: datetime


def calculate_alert_sla(
    *,
    alert_type: str,
    created_at: datetime | None = None,
) -> AlertSLA:
    normalized_type = alert_type.strip().lower()

    if normalized_type not in SLA_MINUTES:
        raise ValueError(
            f"Unsupported alert type: {alert_type}"
        )

    base_time = created_at or datetime.now(
        timezone.utc
    )

    if base_time.tzinfo is None:
        raise ValueError(
            "created_at must be timezone-aware."
        )

    sla_minutes = SLA_MINUTES[
        normalized_type
    ]

    return AlertSLA(
        alert_type=normalized_type,
        sla_minutes=sla_minutes,
        created_at=base_time,
        due_at=base_time
        + timedelta(
            minutes=sla_minutes,
        ),
    )


def is_alert_overdue(
    *,
    sla_due_at: datetime,
    delivered_at: datetime | None = None,
    now: datetime | None = None,
) -> bool:
    if sla_due_at.tzinfo is None:
        raise ValueError(
            "sla_due_at must be timezone-aware."
        )

    current_time = now or datetime.now(
        timezone.utc
    )

    if current_time.tzinfo is None:
        raise ValueError(
            "now must be timezone-aware."
        )

    if delivered_at is not None:
        if delivered_at.tzinfo is None:
            raise ValueError(
                "delivered_at must be timezone-aware."
            )

        return delivered_at > sla_due_at

    return current_time > sla_due_at

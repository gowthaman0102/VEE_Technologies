from dataclasses import dataclass

from sqlalchemy import select

from app.models.monitoring_topic import MonitoringTopic
from app.schemas.article_triage import EventType
from app.services.risk_rule_service import (
    event_type_to_monitoring_topic,
)


DEFAULT_MONITORING_PRIORITY = "medium"


@dataclass(frozen=True)
class MonitoringPriorityResult:
    company_id: int
    event_type: str
    monitoring_topic: str | None
    priority: str
    source: str


async def resolve_monitoring_priority(
    db,
    *,
    company_id: int,
    event_type: EventType,
) -> MonitoringPriorityResult:
    monitoring_topic = (
        event_type_to_monitoring_topic(
            event_type
        )
    )

    if monitoring_topic is None:
        return MonitoringPriorityResult(
            company_id=company_id,
            event_type=event_type,
            monitoring_topic=None,
            priority=DEFAULT_MONITORING_PRIORITY,
            source="fallback",
        )

    result = await db.execute(
        select(MonitoringTopic).where(
            MonitoringTopic.company_id == company_id,
            MonitoringTopic.topic == monitoring_topic,
            MonitoringTopic.is_active.is_(True),
        )
    )

    record = result.scalar_one_or_none()

    if record is None:
        return MonitoringPriorityResult(
            company_id=company_id,
            event_type=event_type,
            monitoring_topic=monitoring_topic,
            priority=DEFAULT_MONITORING_PRIORITY,
            source="fallback",
        )

    return MonitoringPriorityResult(
        company_id=company_id,
        event_type=event_type,
        monitoring_topic=record.topic,
        priority=record.priority.strip().lower(),
        source="configured",
    )

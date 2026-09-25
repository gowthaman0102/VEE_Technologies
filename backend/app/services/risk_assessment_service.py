from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.article_triage_read_service import (
    get_article_triage,
)
from app.services.client_configuration_service import get_client_config
from app.services.monitoring_priority_service import (
    MonitoringPriorityResult,
    resolve_monitoring_priority,
)
from app.services.risk_escalation_service import (
    EscalationDecision,
    decide_escalation,
)
from app.services.risk_rule_service import (
    RiskCalculation,
    calculate_risk,
)
from app.services.risk_assessment_persistence_service import (
    save_risk_assessment,
)


class StoredTriageNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class RiskAssessmentResult:
    triage_id: int
    article_id: int
    company_id: int
    company_name: str
    event_type: str
    urgency: str
    confidence: float
    monitoring_priority: MonitoringPriorityResult
    risk: RiskCalculation
    escalation: EscalationDecision


async def assess_article_risk(
    db,
    *,
    article_id: int,
    company_id: int,
) -> RiskAssessmentResult:
    triage = await get_article_triage(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    if triage is None:
        raise StoredTriageNotFoundError(
            "Stored triage result not found for "
            f"article {article_id} and company {company_id}."
        )

    priority = await resolve_monitoring_priority(
        db,
        company_id=company_id,
        event_type=triage.event_type,
    )

    client_config = None
    if isinstance(db, AsyncSession):
        client_config = await get_client_config(db, company_id)

    risk = calculate_risk(
        event_type=triage.event_type,
        topic_priority=priority.priority,
        urgency=triage.urgency,
        confidence=triage.confidence,
        risk_configuration=(
            client_config.risk
            if client_config is not None
            else None
        ),
    )

    escalation = decide_escalation(
        risk_level=risk.risk_level,
        configuration=(
            client_config.alerts
            if client_config is not None
            else None
        ),
    )

    assessment = RiskAssessmentResult(
        triage_id=triage.id,
        article_id=triage.article_id,
        company_id=triage.company_id,
        company_name=triage.company_name,
        event_type=triage.event_type,
        urgency=triage.urgency,
        confidence=triage.confidence,
        monitoring_priority=priority,
        risk=risk,
        escalation=escalation,
    )

    await save_risk_assessment(
        db,
        assessment=assessment,
    )

    return assessment

from dataclasses import dataclass

from sqlalchemy import select

from app.models.alert import Alert
from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight
from app.services.alert_persistence_service import (
    save_alert,
)
from app.services.alert_rule_service import (
    decide_alert,
)
from app.services.alert_sla_service import (
    calculate_alert_sla,
)


class RiskAssessmentNotFoundError(
    ValueError
):
    pass


class RiskInsightNotFoundError(
    ValueError
):
    pass


@dataclass(frozen=True)
class AlertServiceResult:
    should_create_alert: bool
    alert: Alert | None


async def create_alert_for_intelligence(
    db,
    *,
    article_id: int,
    company_id: int,
) -> AlertServiceResult:
    risk_result = await db.execute(
        select(RiskAssessment).where(
            RiskAssessment.article_id
            == article_id,
            RiskAssessment.company_id
            == company_id,
        )
    )

    risk_record = (
        risk_result.scalar_one_or_none()
    )

    if risk_record is None:
        raise RiskAssessmentNotFoundError(
            "Risk assessment not found for "
            f"article {article_id} and "
            f"company {company_id}."
        )

    decision = decide_alert(
        escalation_action=(
            risk_record.escalation_action
        ),
    )

    if not decision.should_create_alert:
        return AlertServiceResult(
            should_create_alert=False,
            alert=None,
        )

    insight_result = await db.execute(
        select(RiskInsight).where(
            RiskInsight.article_id
            == article_id,
            RiskInsight.company_id
            == company_id,
        )
    )

    insight_record = (
        insight_result.scalar_one_or_none()
    )

    if insight_record is None:
        raise RiskInsightNotFoundError(
            "Risk insight not found for "
            f"article {article_id} and "
            f"company {company_id}."
        )

    sla = calculate_alert_sla(
        alert_type=decision.alert_type,
    )

    message = (
        f"{insight_record.executive_summary}\n\n"
        "Recommended action: "
        f"{insight_record.recommended_action}"
    )

    alert = await save_alert(
        db,
        article_id=article_id,
        company_id=company_id,
        alert_type=decision.alert_type,
        severity=decision.severity,
        title=insight_record.headline,
        message=message,
        requires_immediate_delivery=(
            decision.requires_immediate_delivery
        ),
        sla_due_at=sla.due_at,
    )

    return AlertServiceResult(
        should_create_alert=True,
        alert=alert,
    )

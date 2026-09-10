from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.risk_assessment import RiskAssessment

if TYPE_CHECKING:
    from app.services.risk_assessment_service import (
        RiskAssessmentResult,
    )


async def save_risk_assessment(
    db,
    *,
    assessment: "RiskAssessmentResult",
) -> RiskAssessment:
    result = await db.execute(
        select(RiskAssessment).where(
            RiskAssessment.article_id
            == assessment.article_id,
            RiskAssessment.company_id
            == assessment.company_id,
        )
    )

    record = result.scalar_one_or_none()

    values = {
        "triage_id": assessment.triage_id,
        "event_type": assessment.event_type,
        "monitoring_topic": (
            assessment.monitoring_priority.monitoring_topic
        ),
        "topic_priority": (
            assessment.monitoring_priority.priority
        ),
        "priority_source": (
            assessment.monitoring_priority.source
        ),
        "urgency": assessment.urgency,
        "confidence": assessment.confidence,
        "risk_score": assessment.risk.risk_score,
        "risk_level": assessment.risk.risk_level,
        "escalation_action": (
            assessment.escalation.action
        ),
        "requires_human_review": (
            assessment.escalation.requires_human_review
        ),
        "requires_immediate_alert": (
            assessment.escalation.requires_immediate_alert
        ),
    }

    if record is None:
        record = RiskAssessment(
            article_id=assessment.article_id,
            company_id=assessment.company_id,
            **values,
        )

        db.add(record)

    else:
        for field, value in values.items():
            setattr(
                record,
                field,
                value,
            )

    await db.commit()
    await db.refresh(record)

    return record

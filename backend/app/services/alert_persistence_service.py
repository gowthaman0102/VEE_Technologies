from datetime import datetime

from sqlalchemy import select

from app.models.alert import Alert
from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight


class StoredRiskAssessmentNotFoundError(
    ValueError
):
    pass


async def save_alert(
    db,
    *,
    article_id: int,
    company_id: int,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    requires_immediate_delivery: bool,
    sla_due_at: datetime,
) -> Alert:
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
        raise StoredRiskAssessmentNotFoundError(
            "Stored risk assessment not found for "
            f"article {article_id} and "
            f"company {company_id}."
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

    existing_result = await db.execute(
        select(Alert).where(
            Alert.article_id == article_id,
            Alert.company_id == company_id,
            Alert.alert_type == alert_type,
        )
    )

    record = (
        existing_result.scalar_one_or_none()
    )

    values = {
        "risk_assessment_id": risk_record.id,
        "risk_insight_id": (
            insight_record.id
            if insight_record is not None
            else None
        ),
        "severity": severity,
        "title": title,
        "message": message,
        "requires_immediate_delivery": (
            requires_immediate_delivery
        ),
    }

    if record is None:
        record = Alert(
            article_id=article_id,
            company_id=company_id,
            alert_type=alert_type,
            sla_due_at=sla_due_at,
            delivery_status="pending",
            retry_count=0,
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


async def get_alert(
    db,
    *,
    article_id: int,
    company_id: int,
    alert_type: str,
) -> Alert | None:
    result = await db.execute(
        select(Alert).where(
            Alert.article_id == article_id,
            Alert.company_id == company_id,
            Alert.alert_type == alert_type,
        )
    )

    return result.scalar_one_or_none()

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight

if TYPE_CHECKING:
    from app.services.risk_insight_service import (
        RiskInsightServiceResult,
    )


class StoredRiskAssessmentNotFoundError(
    ValueError
):
    pass


async def save_risk_insight(
    db,
    *,
    result: "RiskInsightServiceResult",
) -> RiskInsight:
    risk_result = await db.execute(
        select(RiskAssessment).where(
            RiskAssessment.article_id
            == result.article_id,
            RiskAssessment.company_id
            == result.company_id,
        )
    )

    risk_record = (
        risk_result.scalar_one_or_none()
    )

    if risk_record is None:
        raise StoredRiskAssessmentNotFoundError(
            "Stored risk assessment not found for "
            f"article {result.article_id} and "
            f"company {result.company_id}."
        )

    insight_result = await db.execute(
        select(RiskInsight).where(
            RiskInsight.article_id
            == result.article_id,
            RiskInsight.company_id
            == result.company_id,
        )
    )

    record = (
        insight_result.scalar_one_or_none()
    )

    values = {
        "risk_assessment_id": risk_record.id,
        "headline": result.insight.headline,
        "executive_summary": (
            result.insight.executive_summary
        ),
        "recommended_action": (
            result.insight.recommended_action
        ),
        "key_reasons": (
            result.insight.key_reasons
        ),
        "attention_level": (
            result.insight.attention_level
        ),
        "llm_model": result.model,
    }

    if record is None:
        record = RiskInsight(
            article_id=result.article_id,
            company_id=result.company_id,
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

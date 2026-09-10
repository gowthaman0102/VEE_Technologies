from sqlalchemy import select

from app.models.risk_assessment import RiskAssessment


async def get_risk_assessment(
    db,
    *,
    article_id: int,
    company_id: int,
) -> RiskAssessment | None:
    result = await db.execute(
        select(RiskAssessment).where(
            RiskAssessment.article_id == article_id,
            RiskAssessment.company_id == company_id,
        )
    )

    return result.scalar_one_or_none()

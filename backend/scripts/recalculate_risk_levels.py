import asyncio
import os

os.chdir(r"D:\VEE_Technologies\backend")

from sqlalchemy import case, update

from app.db.session import engine
from app.models.risk_assessment import RiskAssessment


async def main() -> None:
    async with engine.begin() as conn:
        stmt = (
            update(RiskAssessment)
            .values(
                risk_level=case(
                    (RiskAssessment.risk_score >= 80.0, "critical"),
                    (RiskAssessment.risk_score >= 60.0, "high"),
                    (RiskAssessment.risk_score >= 40.0, "medium"),
                    else_="low",
                ),
                escalation_action=case(
                    (RiskAssessment.risk_score >= 80.0, "escalate"),
                    (RiskAssessment.risk_score >= 60.0, "review"),
                    (RiskAssessment.risk_score >= 40.0, "monitor"),
                    else_="ignore",
                ),
                requires_human_review=case(
                    (RiskAssessment.risk_score >= 60.0, True),
                    else_=False,
                ),
                requires_immediate_alert=case(
                    (RiskAssessment.risk_score >= 80.0, True),
                    else_=False,
                ),
            )
        )
        result = await conn.execute(stmt)
        print(f"UPDATED_ROWS={result.rowcount}")


if __name__ == "__main__":
    asyncio.run(main())

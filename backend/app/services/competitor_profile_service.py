from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_relationship import (
    CompanyRelationship,
)


@dataclass(frozen=True)
class CompetitorProfile:
    company_id: int
    competitors: list[str]


async def get_competitor_profile(
    db: AsyncSession,
    *,
    company_id: int,
) -> CompetitorProfile:
    result = await db.execute(
        select(
            CompanyRelationship.related_company_name
        )
        .where(
            CompanyRelationship.company_id
            == company_id,
            CompanyRelationship.relationship_type
            == "competitor",
        )
        .order_by(
            CompanyRelationship.related_company_name
        )
    )

    competitors = [
        name.strip()
        for name in result.scalars().all()
        if name and name.strip()
    ]

    return CompetitorProfile(
        company_id=company_id,
        competitors=competitors,
    )

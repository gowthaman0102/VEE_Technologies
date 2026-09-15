from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.services.company_context_service import (
    get_company_context,
)


@dataclass(frozen=True)
class ActiveCompanyProfile:
    company_id: int
    company_name: str
    aliases: list[str]


async def get_active_company_profile(
    db: AsyncSession,
) -> ActiveCompanyProfile | None:
    result = await db.execute(
        select(Company)
        .where(
            Company.is_active.is_(True)
        )
        .order_by(
            Company.id.asc()
        )
        .limit(1)
    )

    company = result.scalar_one_or_none()

    if company is None:
        return None

    context = await get_company_context(
        db,
        company.id,
    )

    aliases = {
        company.name.strip(),
    }

    for item in context["aliases"]:
        alias = (
            item.alias or ""
        ).strip()

        if alias:
            aliases.add(alias)

    return ActiveCompanyProfile(
        company_id=company.id,
        company_name=company.name,
        aliases=sorted(aliases),
    )

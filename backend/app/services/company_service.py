from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreate


async def create_company(
    db: AsyncSession,
    data: CompanyCreate,
) -> Company:
    company = Company(
        client_id=data.client_id,
        name=data.name,
        website=data.website,
        industry=data.industry,
    )

    db.add(company)
    await db.commit()
    await db.refresh(company)

    return company


async def get_company(
    db: AsyncSession,
    company_id: int,
) -> Company | None:
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )

    return result.scalar_one_or_none()


async def list_companies(
    db: AsyncSession,
) -> list[Company]:
    result = await db.execute(
        select(Company).order_by(Company.id)
    )

    return list(result.scalars().all())


async def list_companies_by_client(
    db: AsyncSession,
    client_id: int,
) -> list[Company]:
    result = await db.execute(
        select(Company)
        .where(Company.client_id == client_id)
        .order_by(Company.id)
    )

    return list(result.scalars().all())



from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_configuration import CompanyConfiguration
from app.services.company_context_service import get_company_context
from app.schemas.client_configuration import (
    AlertConfiguration,
    BrandingConfiguration,
    ClientConfiguration,
    FeatureConfiguration,
    ReportConfiguration,
    RiskConfiguration,
    SourceConfiguration,
)
from app.schemas.client_configuration import ClientConfigurationUpdate


async def get_client_config(
    db: AsyncSession,
    company_id: int,
) -> ClientConfiguration:
    company = await db.scalar(select(Company).where(Company.id == company_id))
    if company is None:
        raise ValueError(f"company {company_id} does not exist")

    context = await get_company_context(db, company_id)
    row = await db.scalar(
        select(CompanyConfiguration).where(
            CompanyConfiguration.company_id == company_id
        )
    )

    return ClientConfiguration(
        company_id=company.id,
        company_name=company.name,
        aliases=sorted({company.name, *(item.alias for item in context["aliases"])}),
        monitoring_topics=[item.topic for item in context["monitoring_topics"] if item.is_active],
        competitors=[
            item.related_company_name
            for item in context["relationships"]
            if item.relationship_type == "competitor"
        ],
        geographies=[item.geography for item in context["geographies"]],
        regulators=[item.regulator for item in context["regulators"]],
        sources=SourceConfiguration.model_validate(row.sources if row and row.sources else {}),
        risk=RiskConfiguration.model_validate(row.risk if row and row.risk else {}),
        alerts=AlertConfiguration.model_validate(row.alerts if row and row.alerts else {}),
        reports=ReportConfiguration.model_validate(row.reports if row and row.reports else {}),
        features=FeatureConfiguration.model_validate(row.features if row and row.features else {}),
        branding=BrandingConfiguration.model_validate(row.branding if row and row.branding else {}),
    )


async def update_client_config(
    db: AsyncSession,
    company_id: int,
    data: ClientConfigurationUpdate,
) -> ClientConfiguration:
    company = await db.scalar(select(Company).where(Company.id == company_id))
    if company is None:
        raise ValueError(f"company {company_id} does not exist")

    row = await db.scalar(
        select(CompanyConfiguration).where(
            CompanyConfiguration.company_id == company_id
        )
    )
    if row is None:
        row = CompanyConfiguration(company_id=company_id)
        db.add(row)

    for section in ("sources", "risk", "alerts", "reports", "features", "branding"):
        value = getattr(data, section)
        if value is not None:
            setattr(row, section, value.model_dump(mode="json"))

    await db.commit()
    return await get_client_config(db, company_id)

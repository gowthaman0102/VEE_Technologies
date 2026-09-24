from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.company import Company
from app.models.company_alias import CompanyAlias
from app.models.company_geography import CompanyGeography
from app.models.company_location import CompanyLocation
from app.models.risk_assessment import RiskAssessment
from app.schemas.company_overview import (
    CompanyOverviewHealth,
    CompanyOverviewProfile,
    CompanyOverviewResponse,
    CompanyOverviewSentiment,
    CompanyLocationCountry,
    CompanyLocationResponse,
)


async def get_company_overview(
    db: AsyncSession,
    company_id: int,
) -> CompanyOverviewResponse | None:
    company = await db.scalar(select(Company).where(Company.id == company_id))
    if company is None:
        return None

    aliases = list(
        await db.scalars(
            select(CompanyAlias.alias)
            .where(CompanyAlias.company_id == company_id)
            .order_by(CompanyAlias.alias)
        )
    )
    geographies = list(
        await db.scalars(
            select(CompanyGeography.geography)
            .where(CompanyGeography.company_id == company_id)
            .order_by(CompanyGeography.geography)
        )
    )

    total_articles = int(
        await db.scalar(
            select(func.count(ArticleTriage.id)).where(
                ArticleTriage.company_id == company_id
            )
        )
        or 0
    )
    sentiment_rows = await db.execute(
        select(
            func.lower(ArticleSentiment.label),
            func.count(ArticleSentiment.id),
        )
        .join(
            ArticleTriage,
            ArticleTriage.article_id == ArticleSentiment.article_id,
        )
        .where(ArticleTriage.company_id == company_id)
        .where(ArticleSentiment.company_id == company_id)
        .group_by(func.lower(ArticleSentiment.label))
    )
    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for label, count in sentiment_rows:
        if label in sentiment:
            sentiment[label] = int(count)

    high_risk_count = int(
        await db.scalar(
            select(func.count(RiskAssessment.id)).where(
                RiskAssessment.company_id == company_id,
                RiskAssessment.risk_level == "high",
            )
        )
        or 0
    )
    critical_risk_count = int(
        await db.scalar(
            select(func.count(RiskAssessment.id)).where(
                RiskAssessment.company_id == company_id,
                RiskAssessment.risk_level == "critical",
            )
        )
        or 0
    )
    active_alerts = int(
        await db.scalar(
            select(func.count(Alert.id)).where(Alert.company_id == company_id)
        )
        or 0
    )

    location_rows = await db.scalars(
        select(CompanyLocation)
        .where(
            CompanyLocation.company_id == company_id,
            CompanyLocation.verified.is_(True),
        )
        .order_by(CompanyLocation.location_type, CompanyLocation.name)
    )
    locations = list(location_rows)
    location_response = [
        CompanyLocationResponse(
            id=location.id,
            label=location.name,
            location_type=location.location_type,
            city=location.city,
            region=location.region,
            country=location.country,
            latitude=location.latitude,
            longitude=location.longitude,
        )
        for location in locations
    ]
    locations_by_country: dict[str, list[CompanyLocationResponse]] = {}
    for location in location_response:
        locations_by_country.setdefault(location.country, []).append(location)
    official_locations = [
        CompanyLocationCountry(country=country, locations=country_locations)
        for country, country_locations in sorted(
            locations_by_country.items(), key=lambda item: item[0].lower()
        )
    ]
    headquarters = [
        location for location in location_response
        if location.location_type == "headquarters"
    ]

    return CompanyOverviewResponse(
        company=CompanyOverviewProfile(
            id=company.id,
            name=company.name,
            industry=company.industry,
            website=company.website,
            is_active=company.is_active,
            aliases=aliases,
            geographies=geographies,
        ),
        health=CompanyOverviewHealth(
            total_articles=total_articles,
            processed_articles=total_articles,
            sentiment=CompanyOverviewSentiment(**sentiment),
            high_risk_count=high_risk_count,
            critical_risk_count=critical_risk_count,
            active_alerts=active_alerts,
        ),
        official_locations=official_locations,
        headquarters=headquarters,
        official_location_count=len(location_response),
        location_country_count=len(official_locations),
    )

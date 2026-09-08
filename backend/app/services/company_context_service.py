from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_alias import CompanyAlias
from app.models.company_geography import CompanyGeography
from app.models.company_regulator import CompanyRegulator
from app.models.company_relationship import CompanyRelationship
from app.models.monitoring_topic import MonitoringTopic
from app.schemas.company_context import CompanyContextCreate


async def create_company_context(
    db: AsyncSession,
    company_id: int,
    data: CompanyContextCreate,
) -> dict:
    aliases = [
        CompanyAlias(
            company_id=company_id,
            alias=item.alias,
        )
        for item in data.aliases
    ]

    geographies = [
        CompanyGeography(
            company_id=company_id,
            geography=item.geography,
        )
        for item in data.geographies
    ]

    regulators = [
        CompanyRegulator(
            company_id=company_id,
            regulator=item.regulator,
        )
        for item in data.regulators
    ]

    relationships = [
        CompanyRelationship(
            company_id=company_id,
            related_company_name=item.related_company_name,
            relationship_type=item.relationship_type,
        )
        for item in data.relationships
    ]

    monitoring_topics = [
        MonitoringTopic(
            company_id=company_id,
            topic=item.topic,
            priority=item.priority,
        )
        for item in data.monitoring_topics
    ]

    db.add_all(
        aliases
        + geographies
        + regulators
        + relationships
        + monitoring_topics
    )

    await db.commit()

    for item in (
        aliases
        + geographies
        + regulators
        + relationships
        + monitoring_topics
    ):
        await db.refresh(item)

    return {
        "company_id": company_id,
        "aliases": aliases,
        "geographies": geographies,
        "regulators": regulators,
        "relationships": relationships,
        "monitoring_topics": monitoring_topics,
    }


async def get_company_context(
    db: AsyncSession,
    company_id: int,
) -> dict:
    aliases_result = await db.execute(
        select(CompanyAlias)
        .where(CompanyAlias.company_id == company_id)
        .order_by(CompanyAlias.id)
    )

    geographies_result = await db.execute(
        select(CompanyGeography)
        .where(CompanyGeography.company_id == company_id)
        .order_by(CompanyGeography.id)
    )

    regulators_result = await db.execute(
        select(CompanyRegulator)
        .where(CompanyRegulator.company_id == company_id)
        .order_by(CompanyRegulator.id)
    )

    relationships_result = await db.execute(
        select(CompanyRelationship)
        .where(CompanyRelationship.company_id == company_id)
        .order_by(CompanyRelationship.id)
    )

    topics_result = await db.execute(
        select(MonitoringTopic)
        .where(MonitoringTopic.company_id == company_id)
        .order_by(MonitoringTopic.id)
    )

    return {
        "company_id": company_id,
        "aliases": list(aliases_result.scalars().all()),
        "geographies": list(geographies_result.scalars().all()),
        "regulators": list(regulators_result.scalars().all()),
        "relationships": list(relationships_result.scalars().all()),
        "monitoring_topics": list(topics_result.scalars().all()),
    }

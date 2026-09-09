from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.company_context_service import (
    get_company_context,
)
from app.services.company_service import (
    get_company,
)


@dataclass(frozen=True)
class CompanySemanticContext:
    company_id: int
    company_name: str
    text: str


async def build_company_semantic_context(
    db: AsyncSession,
    company_id: int,
) -> CompanySemanticContext | None:
    company = await get_company(
        db,
        company_id,
    )

    if company is None:
        return None

    context = await get_company_context(
        db,
        company_id,
    )

    lines: list[str] = [
        f"Company: {company.name.strip()}",
    ]

    if company.industry:
        industry = company.industry.strip()

        if industry:
            lines.append(
                f"Industry: {industry}"
            )

    aliases = [
        item.alias.strip()
        for item in context["aliases"]
        if item.alias and item.alias.strip()
    ]

    if aliases:
        lines.append(
            "Aliases: " + ", ".join(aliases)
        )

    geographies = [
        item.geography.strip()
        for item in context["geographies"]
        if item.geography
        and item.geography.strip()
    ]

    if geographies:
        lines.append(
            "Geographies: "
            + ", ".join(geographies)
        )

    regulators = [
        item.regulator.strip()
        for item in context["regulators"]
        if item.regulator
        and item.regulator.strip()
    ]

    if regulators:
        lines.append(
            "Regulators: "
            + ", ".join(regulators)
        )

    relationships = []

    for item in context["relationships"]:
        related_name = (
            item.related_company_name or ""
        ).strip()

        relationship_type = (
            item.relationship_type or ""
        ).strip()

        if not related_name:
            continue

        if relationship_type:
            relationships.append(
                f"{relationship_type}: {related_name}"
            )
        else:
            relationships.append(
                related_name
            )

    if relationships:
        lines.append(
            "Relationships: "
            + "; ".join(relationships)
        )

    topics = []

    for item in context["monitoring_topics"]:
        topic = (
            item.topic or ""
        ).strip()

        priority = (
            item.priority or ""
        ).strip()

        if not topic:
            continue

        if priority:
            topics.append(
                f"{topic} [{priority}]"
            )
        else:
            topics.append(topic)

    if topics:
        lines.append(
            "Monitoring topics: "
            + "; ".join(topics)
        )

    return CompanySemanticContext(
        company_id=company.id,
        company_name=company.name,
        text="\n".join(lines),
    )

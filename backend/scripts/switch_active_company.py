import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.models.alert import Alert
from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_competitor_mention import ArticleCompetitorMention
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.company import Company
from app.models.company_alias import CompanyAlias
from app.models.company_geography import CompanyGeography
from app.models.company_regulator import CompanyRegulator
from app.models.company_relationship import CompanyRelationship
from app.models.event_cluster import EventCluster, EventClusterMembership
from app.models.generated_report import GeneratedReport
from app.models.monitoring_topic import MonitoringTopic
from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight
from app.models.watchlist import WatchlistItem


ARTICLE_LINKED_MODELS = (
    ArticleTriage,
    ArticleSentiment,
    ArticleBusinessImpact,
    ArticleCompetitorMention,
    RiskAssessment,
    RiskInsight,
    EventClusterMembership,
    Alert,
)
COMPANY_LINKED_MODELS = (
    EventCluster,
    GeneratedReport,
    WatchlistItem,
)
CONTEXT_MODELS = (
    CompanyAlias,
    CompanyGeography,
    CompanyRegulator,
    CompanyRelationship,
    MonitoringTopic,
)


def serialize(value):
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def serialize_row(instance) -> dict:
    return {
        column.name: serialize(getattr(instance, column.name))
        for column in instance.__table__.columns
    }


async def export_vee_rows(db, vee: Company, article_ids: list[int], output: Path) -> None:
    payload = {
        "exported_at": datetime.now().astimezone().isoformat(),
        "company": serialize_row(vee),
        "articles": [],
        "article_linked": {},
        "company_linked": {},
        "context": {},
    }

    if article_ids:
        result = await db.execute(
            select(Article).where(Article.id.in_(article_ids)).order_by(Article.id)
        )
        payload["articles"] = [serialize_row(item) for item in result.scalars().all()]

    for model in ARTICLE_LINKED_MODELS:
        conditions = [model.company_id == vee.id]
        if hasattr(model, "article_id") and article_ids:
            conditions.append(model.article_id.in_(article_ids))
        result = await db.execute(select(model).where(conditions[0]))
        rows = result.scalars().all()
        if len(conditions) > 1:
            result = await db.execute(
                select(model).where(
                    (model.company_id == vee.id) | model.article_id.in_(article_ids)
                )
            )
            rows = result.scalars().all()
        payload["article_linked"][model.__tablename__] = [serialize_row(item) for item in rows]

    for model in COMPANY_LINKED_MODELS:
        result = await db.execute(
            select(model).where(model.company_id == vee.id)
        )
        payload["company_linked"][model.__tablename__] = [
            serialize_row(item) for item in result.scalars().all()
        ]

    for model in CONTEXT_MODELS:
        result = await db.execute(
            select(model).where(model.company_id == vee.id)
        )
        payload["context"][model.__tablename__] = [
            serialize_row(item) for item in result.scalars().all()
        ]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def run(*, execute: bool, backup_path: Path) -> None:
    async with AsyncSessionLocal() as db:
        companies = (
            await db.execute(select(Company).order_by(Company.id))
        ).scalars().all()
        vee = next((item for item in companies if item.name.casefold() == "vee technologies".casefold()), None)
        if vee is None:
            raise RuntimeError("VEE Technologies company was not found")

        article_ids = set(
            (
                await db.execute(
                    select(Article.id).where(
                        Article.source_name.ilike("%VEE Technologies%")
                    )
                )
            ).scalars().all()
        )
        for model in ARTICLE_LINKED_MODELS:
            if hasattr(model, "company_id") and hasattr(model, "article_id"):
                rows = await db.execute(
                    select(model.article_id).where(model.company_id == vee.id)
                )
                article_ids.update(rows.scalars().all())

        await export_vee_rows(db, vee, sorted(article_ids), backup_path)
        print("BACKUP", backup_path)
        print("VEE_ARTICLES_BEFORE", len(article_ids))

        if not execute:
            print("DRY_RUN True")
            return

        openai = next((item for item in companies if item.name.casefold() == "openai"), None)
        if openai is None:
            openai = Company(
                client_id=vee.client_id,
                name="OpenAI",
                website="https://openai.com",
                industry="Artificial intelligence",
                is_active=True,
            )
            db.add(openai)
            await db.flush()
        else:
            openai.website = "https://openai.com"
            openai.industry = "Artificial intelligence"

        for company in companies:
            company.is_active = company.id == openai.id

        await db.execute(
            delete(Article).where(Article.id.in_(sorted(article_ids)))
        )
        await db.execute(delete(EventCluster).where(EventCluster.company_id == vee.id))
        await db.execute(delete(GeneratedReport).where(GeneratedReport.company_id == vee.id))

        for model in CONTEXT_MODELS + (WatchlistItem,):
            await db.execute(delete(model).where(model.company_id == openai.id))

        aliases = ["OpenAI", "OpenAI, Inc.", "OpenAI LP", "ChatGPT"]
        db.add_all([
            CompanyAlias(company_id=openai.id, alias=value)
            for value in aliases
        ])

        topics = {
            "AI Safety": "high",
            "Cybersecurity": "high",
            "Regulatory Development": "high",
            "Data Privacy": "high",
            "Legal": "high",
            "Reputation": "high",
            "Model Release": "medium",
            "Product Launch": "medium",
            "Partnership": "medium",
            "Infrastructure": "medium",
            "Enterprise Expansion": "medium",
            "Research Breakthrough": "medium",
            "Developer Platform": "medium",
            "Leadership Change": "medium",
            "Policy": "medium",
            "Education": "low",
            "Scientific Research": "medium",
            "Regulatory Action": "high",
            "Fraud and Security": "high",
            "Service Outage": "high",
            "Financial Performance": "medium",
            "Market Competition": "medium",
        }
        db.add_all([
            MonitoringTopic(company_id=openai.id, topic=topic, priority=priority)
            for topic, priority in topics.items()
        ])

        watchlist = [
            ("company", "OpenAI", "OpenAI"),
            ("product", "ChatGPT", "ChatGPT"),
            ("platform", "API", "API"),
            ("topic", "Model Release", "model release"),
            ("topic", "AI Safety", "safety"),
            ("topic", "Cybersecurity", "security"),
            ("topic", "Partnership", "partnership"),
            ("topic", "Regulatory Development", "regulation"),
        ]
        db.add_all([
            WatchlistItem(
                company_id=openai.id,
                item_type=item_type,
                item_name=item_name,
                value=value,
            )
            for item_type, item_name, value in watchlist
        ])

        await db.commit()
        print("ACTIVE_COMPANY", openai.name)
        print("OPENAI_COMPANY_ID", openai.id)
        print("VEE_ARTICLES_REMOVED", len(article_ids))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--backup", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(execute=args.execute, backup_path=args.backup))

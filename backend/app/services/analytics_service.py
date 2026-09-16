from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.company import Company
from app.models.company_relationship import CompanyRelationship
from app.models.event_cluster import EventCluster, EventClusterMembership
from app.models.risk_assessment import RiskAssessment


SUPPORTED_IMPACT_CATEGORIES = [
    "financial",
    "operational",
    "legal",
    "regulatory",
    "cybersecurity",
    "reputation",
    "customer",
    "product",
    "market",
    "competitive",
]


def validate_time_window(
    start: datetime,
    end: datetime,
    *,
    allow_future: bool = False,
) -> tuple[datetime, datetime]:
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start and end must be timezone-aware")

    if start > end:
        raise ValueError("start date must be before end date")

    if not allow_future:
        now = datetime.now(timezone.utc)
        if end > now:
            raise ValueError("end date cannot be in the future")

    return start, end


async def get_article_volume_over_time(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
    bucket: str = "day",
) -> list[dict]:
    start, end = validate_time_window(start, end)

    if bucket not in {"hour", "day", "week", "month"}:
        raise ValueError("Unsupported bucket")

    article_table = Article
    date_expr = {
        "hour": func.date_trunc("hour", article_table.published_at),
        "day": func.date_trunc("day", article_table.published_at),
        "week": func.date_trunc("week", article_table.published_at),
        "month": func.date_trunc("month", article_table.published_at),
    }[bucket]

    stmt = (
        select(
            date_expr.label("bucket"),
            func.count(article_table.id).label("article_count"),
        )
        .join(
            ArticleTriage,
            ArticleTriage.article_id == article_table.id,
        )
        .where(
            ArticleTriage.company_id == company_id,
            article_table.published_at.is_not(None),
            article_table.published_at >= start,
            article_table.published_at <= end,
        )
        .group_by(date_expr)
        .order_by(date_expr.asc())
    )

    result = await db.execute(stmt)
    return [
        {
            "bucket": row.bucket.isoformat() if row.bucket else None,
            "article_count": int(row.article_count),
        }
        for row in result.all()
    ]


async def get_sentiment_distribution(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    stmt = (
        select(
            ArticleSentiment.label,
            func.count(ArticleSentiment.id).label("count"),
        )
        .where(
            ArticleSentiment.company_id == company_id,
            ArticleSentiment.created_at >= start,
            ArticleSentiment.created_at <= end,
        )
        .group_by(ArticleSentiment.label)
    )

    result = await db.execute(stmt)
    summary = {row.label: int(row.count) for row in result.all()}
    return {
        "positive": summary.get("positive", 0),
        "neutral": summary.get("neutral", 0),
        "negative": summary.get("negative", 0),
    }


async def get_risk_summary(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    stmt = (
        select(
            func.avg(RiskAssessment.risk_score).label("average_risk_score"),
            func.max(RiskAssessment.risk_score).label("highest_risk_score"),
            func.count(
                func.case(
                    (RiskAssessment.risk_level == "high", 1),
                    else_=None,
                )
            ).label("high_risk_count"),
            func.count(
                func.case(
                    (RiskAssessment.risk_level == "medium", 1),
                    else_=None,
                )
            ).label("medium_risk_count"),
            func.count(
                func.case(
                    (RiskAssessment.risk_level == "low", 1),
                    else_=None,
                )
            ).label("low_risk_count"),
        )
        .where(
            RiskAssessment.company_id == company_id,
            RiskAssessment.created_at >= start,
            RiskAssessment.created_at <= end,
        )
    )

    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        return {
            "average_risk_score": 0.0,
            "highest_risk_score": 0.0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
        }

    return {
        "average_risk_score": float(row.average_risk_score or 0.0),
        "highest_risk_score": float(row.highest_risk_score or 0.0),
        "high_risk_count": int(row.high_risk_count or 0),
        "medium_risk_count": int(row.medium_risk_count or 0),
        "low_risk_count": int(row.low_risk_count or 0),
    }


async def get_business_impact_distribution(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    stmt = (
        select(
            ArticleBusinessImpact.primary_category,
            func.count(ArticleBusinessImpact.id).label("count"),
        )
        .where(
            ArticleBusinessImpact.company_id == company_id,
            ArticleBusinessImpact.created_at >= start,
            ArticleBusinessImpact.created_at <= end,
        )
        .group_by(ArticleBusinessImpact.primary_category)
    )

    rows = (await db.execute(stmt)).all()
    return {row.primary_category: int(row.count) for row in rows}


async def get_event_summary(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    cluster_stmt = (
        select(
            EventCluster.id,
            EventCluster.title,
            EventCluster.first_published_at,
            EventCluster.last_published_at,
            func.count(EventClusterMembership.article_id).label("article_count"),
        )
        .join(
            EventClusterMembership,
            EventClusterMembership.cluster_id == EventCluster.id,
        )
        .where(
            EventCluster.company_id == company_id,
            EventCluster.first_published_at >= start,
            EventCluster.last_published_at <= end,
        )
        .group_by(
            EventCluster.id,
            EventCluster.title,
            EventCluster.first_published_at,
            EventCluster.last_published_at,
        )
        .order_by(func.count(EventClusterMembership.article_id).desc())
    )

    rows = (await db.execute(cluster_stmt)).all()
    total_events = len(rows)
    largest_events = [
        {
            "cluster_id": row.id,
            "title": row.title,
            "article_count": int(row.article_count),
            "first_published_at": row.first_published_at,
            "last_published_at": row.last_published_at,
        }
        for row in rows
    ]

    return {
        "total_events": total_events,
        "largest_events": largest_events,
    }


async def get_source_summary(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    stmt = (
        select(
            Article.source_name,
            func.count(Article.id).label("article_count"),
        )
        .join(
            ArticleTriage,
            ArticleTriage.article_id == Article.id,
        )
        .where(
            ArticleTriage.company_id == company_id,
            Article.source_name.is_not(None),
            Article.published_at >= start,
            Article.published_at <= end,
        )
        .group_by(Article.source_name)
        .order_by(func.count(Article.id).desc())
    )

    rows = (await db.execute(stmt)).all()
    return {
        "sources": [
            {"source_name": row.source_name, "article_count": int(row.article_count)}
            for row in rows
        ]
    }


async def get_competitor_summary(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    stmt = (
        select(
            CompanyRelationship.related_company_name.label("competitor"),
            func.count(CompanyRelationship.id).label("mention_count"),
        )
        .where(
            CompanyRelationship.company_id == company_id,
            CompanyRelationship.relationship_type == "competitor",
        )
        .group_by(CompanyRelationship.related_company_name)
    )

    rows = (await db.execute(stmt)).all()
    competitors = [
        {"name": row.competitor, "mention_count": int(row.mention_count)}
        for row in rows
    ]

    if not competitors:
        return {"competitors": []}

    return {"competitors": competitors}

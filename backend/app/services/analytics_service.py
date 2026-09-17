from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_competitor_mention import ArticleCompetitorMention
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


async def get_article_count(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> int:
    start, end = validate_time_window(start, end)
    stmt = (
        select(func.count(func.distinct(Article.id)))
        .join(ArticleTriage, ArticleTriage.article_id == Article.id)
        .where(
            ArticleTriage.company_id == company_id,
            Article.published_at >= start,
            Article.published_at <= end,
        )
    )
    return int((await db.scalar(stmt)) or 0)


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


def _time_bucket(value: datetime, bucket: str) -> str:
    if bucket == "hour":
        value = value.replace(minute=0, second=0, microsecond=0)
    elif bucket == "week":
        value = value.replace(hour=0, minute=0, second=0, microsecond=0)
        value = value - timedelta(days=value.weekday())
    elif bucket == "month":
        value = value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        value = value.replace(hour=0, minute=0, second=0, microsecond=0)
    return value.isoformat()


def _series_bucket(start: datetime, end: datetime, bucket: str) -> str:
    duration = end - start
    if bucket == "auto":
        if duration <= timedelta(days=1):
            return "hour"
        if duration >= timedelta(days=60):
            return "week"
        return "day"
    return bucket


def percentage_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return round(((current - previous) / previous) * 100, 2)


async def get_period_comparison(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict[str, float | int]:
    start, end = validate_time_window(start, end)
    duration = end - start
    previous_end = start
    previous_start = start - duration
    current_articles = await get_article_count(
        db, company_id=company_id, start=start, end=end
    )
    previous_articles = await get_article_count(
        db, company_id=company_id, start=previous_start, end=previous_end
    )
    current_risk = await get_risk_summary(
        db, company_id=company_id, start=start, end=end
    )
    previous_risk = await get_risk_summary(
        db, company_id=company_id, start=previous_start, end=previous_end
    )
    current_events = await get_event_summary(
        db, company_id=company_id, start=start, end=end
    )
    previous_events = await get_event_summary(
        db, company_id=company_id, start=previous_start, end=previous_end
    )
    return {
        "article_volume_change_percent": percentage_change(current_articles, previous_articles),
        "risk_average_change_percent": percentage_change(
            current_risk["average_risk_score"], previous_risk["average_risk_score"]
        ),
        "event_count_change_percent": percentage_change(
            current_events["total_events"], previous_events["total_events"]
        ),
    }


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

    article_time = func.coalesce(
        Article.published_at,
        Article.collected_at,
    )

    stmt = (
        select(
            ArticleSentiment.label,
            func.count(ArticleSentiment.id).label("count"),
        )
        .join(
            Article,
            Article.id == ArticleSentiment.article_id,
        )
        .where(
            ArticleSentiment.company_id == company_id,
            article_time >= start,
            article_time <= end,
        )
        .group_by(ArticleSentiment.label)
    )

    result = await db.execute(stmt)
    summary = {row.label: int(row.count) for row in result.all()}
    rows = (await db.execute(
        select(
            ArticleSentiment.label,
            article_time.label("article_time"),
        )
        .join(
            Article,
            Article.id == ArticleSentiment.article_id,
        )
        .where(
            ArticleSentiment.company_id == company_id,
            article_time >= start,
            article_time <= end,
        )
    )).all()
    bucket = _series_bucket(start, end, "auto")
    series_map: dict[str, dict[str, int]] = defaultdict(
        lambda: {"positive": 0, "neutral": 0, "negative": 0}
    )
    for label, article_time_value in rows:
        series_map[_time_bucket(article_time_value, bucket)][label] = (
            series_map[_time_bucket(article_time_value, bucket)].get(label, 0) + 1
        )
    summary_payload = {
        "positive": summary.get("positive", 0),
        "neutral": summary.get("neutral", 0),
        "negative": summary.get("negative", 0),
    }
    return {
        "summary": summary_payload,
        "positive": summary_payload["positive"],
        "neutral": summary_payload["neutral"],
        "negative": summary_payload["negative"],
        "series": [
            {"period": period, **values}
            for period, values in sorted(series_map.items())
        ],
    }


async def get_risk_summary(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    article_time = func.coalesce(
        Article.published_at,
        Article.collected_at,
    )

    stmt = (
        select(
            func.avg(RiskAssessment.risk_score).label("average_risk_score"),
            func.max(RiskAssessment.risk_score).label("highest_risk_score"),
            func.count(
                case(
                    (RiskAssessment.risk_level == "high", 1),
                    else_=None,
                )
            ).label("high_risk_count"),
            func.count(
                case(
                    (RiskAssessment.risk_level == "medium", 1),
                    else_=None,
                )
            ).label("medium_risk_count"),
            func.count(
                case(
                    (RiskAssessment.risk_level == "low", 1),
                    else_=None,
                )
            ).label("low_risk_count"),
        )
        .join(
            Article,
            Article.id == RiskAssessment.article_id,
        )
        .where(
            RiskAssessment.company_id == company_id,
            article_time >= start,
            article_time <= end,
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

    summary_payload = {
        "average_risk_score": float(row.average_risk_score or 0.0),
        "highest_risk_score": float(row.highest_risk_score or 0.0),
        "high_risk_count": int(row.high_risk_count or 0),
        "medium_risk_count": int(row.medium_risk_count or 0),
        "low_risk_count": int(row.low_risk_count or 0),
    }
    series = await _get_risk_series(
        db, company_id=company_id, start=start, end=end
    )
    return {
        "summary": summary_payload,
        "average_risk_score": summary_payload["average_risk_score"],
        "highest_risk_score": summary_payload["highest_risk_score"],
        "high_risk_count": summary_payload["high_risk_count"],
        "medium_risk_count": summary_payload["medium_risk_count"],
        "low_risk_count": summary_payload["low_risk_count"],
        "series": series,
    }


async def _get_risk_series(db, *, company_id: int, start: datetime, end: datetime) -> list[dict]:
    article_time = func.coalesce(
        Article.published_at,
        Article.collected_at,
    )

    rows = (await db.execute(
        select(
            article_time.label("article_time"),
            RiskAssessment.risk_score,
            RiskAssessment.risk_level,
            RiskAssessment.escalation_action,
        )
        .join(
            Article,
            Article.id == RiskAssessment.article_id,
        )
        .where(
            RiskAssessment.company_id == company_id,
            article_time >= start,
            article_time <= end,
        )
    )).all()
    bucket = _series_bucket(start, end, "auto")
    grouped: dict[str, list] = defaultdict(list)
    for row in rows:
        grouped[_time_bucket(row.article_time, bucket)].append(row)
    return [
        {
            "period": period,
            "average_risk_score": sum(float(item.risk_score) for item in values) / len(values),
            "maximum_risk_score": max(float(item.risk_score) for item in values),
            "low_count": sum(item.risk_level == "low" for item in values),
            "medium_count": sum(item.risk_level == "medium" for item in values),
            "high_count": sum(item.risk_level == "high" for item in values),
            "escalation_count": sum(item.escalation_action not in {"none", "monitor"} for item in values),
        }
        for period, values in sorted(grouped.items())
    ]


async def get_business_impact_distribution(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime,
    end: datetime,
) -> dict:
    start, end = validate_time_window(start, end)

    article_time = func.coalesce(
        Article.published_at,
        Article.collected_at,
    )

    rows = (
        await db.execute(
            select(
                ArticleBusinessImpact.primary_category,
                ArticleBusinessImpact.categories,
                article_time.label("article_time"),
            )
            .join(
                Article,
                Article.id == ArticleBusinessImpact.article_id,
            )
            .where(
                ArticleBusinessImpact.company_id == company_id,
                article_time >= start,
                article_time <= end,
            )
        )
    ).all()

    primary_counts = {
        category: 0
        for category in SUPPORTED_IMPACT_CATEGORIES
    }

    category_counts = {
        category: 0
        for category in SUPPORTED_IMPACT_CATEGORIES
    }

    bucket = _series_bucket(start, end, "auto")

    primary_series: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    category_series: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for row in rows:
        primary = row.primary_category

        if primary in primary_counts:
            primary_counts[primary] += 1

        period = _time_bucket(
            row.article_time,
            bucket,
        )

        if primary in primary_counts:
            primary_series[period][primary] += 1

        categories = row.categories or []

        # Defensive de-duplication within a single article.
        # One article should count at most once per category.
        unique_categories = {
            category
            for category in categories
            if category in SUPPORTED_IMPACT_CATEGORIES
        }

        for category in unique_categories:
            category_counts[category] += 1
            category_series[period][category] += 1

    return {
        # Preserve "items" for existing frontend/API compatibility.
        "items": primary_counts,
        "primary_distribution": primary_counts,
        "category_distribution": category_counts,
        "series": [
            {
                "period": period,
                "categories": dict(values),
            }
            for period, values in sorted(
                primary_series.items()
            )
        ],
        "category_series": [
            {
                "period": period,
                "categories": dict(values),
            }
            for period, values in sorted(
                category_series.items()
            )
        ],
    }


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
            EventCluster.last_published_at >= start,
            EventCluster.first_published_at <= end,
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
            ArticleSentiment.label,
            RiskAssessment.risk_score,
            RiskAssessment.risk_level,
            EventClusterMembership.cluster_id,
        )
        .join(ArticleTriage, ArticleTriage.article_id == Article.id)
        .outerjoin(
            ArticleSentiment,
            (ArticleSentiment.article_id == Article.id)
            & (ArticleSentiment.company_id == company_id),
        )
        .outerjoin(
            RiskAssessment,
            (RiskAssessment.article_id == Article.id)
            & (RiskAssessment.company_id == company_id),
        )
        .outerjoin(
            EventClusterMembership,
            (EventClusterMembership.article_id == Article.id)
            & (EventClusterMembership.company_id == company_id),
        )
        .where(
            ArticleTriage.company_id == company_id,
            Article.source_name.is_not(None),
            Article.published_at >= start,
            Article.published_at <= end,
        )
    )
    rows = (await db.execute(stmt)).all()
    aggregates: dict[str, dict] = {}
    for source, sentiment, risk_score, risk_level, cluster_id in rows:
        item = aggregates.setdefault(
            source,
            {
                "source_name": source,
                "article_count": 0,
                "sentiment": defaultdict(int),
                "average_risk_score": [],
                "high_risk_count": 0,
                "event_count": set(),
            },
        )
        item["article_count"] += 1
        if sentiment:
            item["sentiment"][sentiment] += 1
        if risk_score is not None:
            item["average_risk_score"].append(float(risk_score))
        if risk_level == "high":
            item["high_risk_count"] += 1
        if cluster_id is not None:
            item["event_count"].add(cluster_id)
    return {
        "sources": [
            {
                "source_name": item["source_name"],
                "article_count": item["article_count"],
                "sentiment": dict(item["sentiment"]),
                "average_risk_score": round(
                    sum(item["average_risk_score"])
                    / len(item["average_risk_score"]),
                    2,
                )
                if item["average_risk_score"]
                else 0.0,
                "high_risk_count": item["high_risk_count"],
                "event_count": len(item["event_count"]),
            }
            for item in sorted(
                aggregates.values(),
                key=lambda value: value["article_count"],
                reverse=True,
            )
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

    configured = (await db.execute(
        select(CompanyRelationship.related_company_name).where(
            CompanyRelationship.company_id == company_id,
            CompanyRelationship.relationship_type == "competitor",
        )
    )).scalars().all()
    if not configured:
        return {"competitors": []}

    rows = (await db.execute(
        select(
            ArticleCompetitorMention.competitors,
            Article.published_at,
            Article.source_name,
            ArticleSentiment.label,
            RiskAssessment.risk_level,
            ArticleBusinessImpact.primary_category,
        )
        .join(Article, Article.id == ArticleCompetitorMention.article_id)
        .outerjoin(ArticleSentiment, (ArticleSentiment.article_id == Article.id) & (ArticleSentiment.company_id == company_id))
        .outerjoin(RiskAssessment, (RiskAssessment.article_id == Article.id) & (RiskAssessment.company_id == company_id))
        .outerjoin(ArticleBusinessImpact, (ArticleBusinessImpact.article_id == Article.id) & (ArticleBusinessImpact.company_id == company_id))
        .where(
            ArticleCompetitorMention.company_id == company_id,
            Article.published_at >= start,
            Article.published_at <= end,
        )
    )).all()
    aggregates = {
        name: {
            "name": name,
            "mention_count": 0,
            "mentions_by_period": defaultdict(int),
            "sentiment": defaultdict(int),
            "risk": defaultdict(int),
            "business_impact": defaultdict(int),
            "sources": defaultdict(int),
        }
        for name in configured
    }
    bucket = _series_bucket(start, end, "auto")
    for competitors, published_at, source_name, sentiment, risk, impact in rows:
        for name in competitors or []:
            if name not in aggregates:
                continue
            item = aggregates[name]
            item["mention_count"] += 1
            if published_at:
                item["mentions_by_period"][_time_bucket(published_at, bucket)] += 1
            if sentiment:
                item["sentiment"][sentiment] += 1
            if risk:
                item["risk"][risk] += 1
            if impact:
                item["business_impact"][impact] += 1
            if source_name:
                item["sources"][source_name] += 1
    for item in aggregates.values():
        item["mentions_by_period"] = dict(sorted(item["mentions_by_period"].items()))
        item["sentiment"] = dict(item["sentiment"])
        item["risk"] = dict(item["risk"])
        item["business_impact"] = dict(item["business_impact"])
        item["sources"] = dict(item["sources"])
    return {"competitors": list(aggregates.values())}

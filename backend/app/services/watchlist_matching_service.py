from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_triage import ArticleTriage
from app.models.risk_assessment import RiskAssessment
from app.models.watchlist import WatchlistItem


@dataclass(frozen=True)
class WatchlistMatch:
    watchlist_item_id: int
    item_type: str
    item_name: str
    value: str
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None
    event_type: str | None = None
    monitoring_topic: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None


def _normalized(value: str) -> str:
    return value.strip().lower()


def _contains(value: str | None, needle: str) -> bool:
    if value is None:
        return False
    return needle in value.lower()


def _exact(value: str | None, expected: str) -> bool:
    if value is None:
        return False
    return value.strip().lower() == expected


def _matches(
    item: WatchlistItem,
    row,
) -> bool:
    expected = _normalized(item.value)

    if not expected:
        return False

    item_type = _normalized(item.item_type)

    if item_type in {"keyword", "regulator"}:
        return any(
            (
                _contains(row.title, expected),
                _contains(row.description, expected),
                _contains(row.cleaned_content, expected),
            )
        )

    if item_type == "source":
        return _exact(row.source_name, expected)

    if item_type == "topic":
        return (
            _exact(row.monitoring_topic, expected)
            or _exact(row.event_type, expected)
        )

    if item_type == "risk_category":
        return _exact(row.risk_level, expected)

    if item_type == "impact_category":
        return _exact(row.business_impact, expected)

    return False


async def match_watchlist_items(
    db: AsyncSession,
    *,
    company_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
) -> list[WatchlistMatch]:
    if company_id < 1:
        raise ValueError("company_id must be at least 1.")

    if limit < 1:
        raise ValueError("limit must be at least 1.")

    if start is not None and end is not None and start >= end:
        raise ValueError("start must be earlier than end.")

    watchlist_statement = (
        select(WatchlistItem)
        .where(
            WatchlistItem.company_id == company_id,
            WatchlistItem.is_active.is_(True),
        )
        .order_by(WatchlistItem.id)
    )

    watchlist_items = list(
        (
            await db.execute(
                watchlist_statement
            )
        ).scalars().all()
    )

    if not watchlist_items:
        return []

    article_statement = (
        select(
            Article.id.label("article_id"),
            Article.title,
            Article.source_name,
            Article.url,
            Article.published_at,
            Article.description,
            Article.cleaned_content,
            ArticleTriage.event_type,
            RiskAssessment.monitoring_topic,
            RiskAssessment.risk_level,
            RiskAssessment.risk_score,
            ArticleBusinessImpact.primary_category.label(
                "business_impact"
            ),
        )
        .join(
            ArticleTriage,
            and_(
                ArticleTriage.article_id == Article.id,
                ArticleTriage.company_id == company_id,
            ),
        )
        .outerjoin(
            RiskAssessment,
            and_(
                RiskAssessment.article_id == Article.id,
                RiskAssessment.company_id == company_id,
            ),
        )
        .outerjoin(
            ArticleBusinessImpact,
            and_(
                ArticleBusinessImpact.article_id == Article.id,
                ArticleBusinessImpact.company_id == company_id,
            ),
        )
    )

    if start is not None:
        article_statement = article_statement.where(
            Article.published_at >= start
        )

    if end is not None:
        article_statement = article_statement.where(
            Article.published_at < end
        )

    article_statement = article_statement.order_by(
        Article.published_at.desc().nullslast(),
        Article.id.desc(),
    )

    rows = (
        await db.execute(article_statement)
    ).all()

    matches: list[WatchlistMatch] = []

    for row in rows:
        for item in watchlist_items:
            if not _matches(item, row):
                continue

            matches.append(
                WatchlistMatch(
                    watchlist_item_id=item.id,
                    item_type=item.item_type,
                    item_name=item.item_name,
                    value=item.value,
                    article_id=row.article_id,
                    title=row.title,
                    source_name=row.source_name,
                    url=row.url,
                    published_at=row.published_at,
                    event_type=row.event_type,
                    monitoring_topic=row.monitoring_topic,
                    risk_level=row.risk_level,
                    risk_score=(
                        float(row.risk_score)
                        if row.risk_score is not None
                        else None
                    ),
                    business_impact=row.business_impact,
                )
            )

            if len(matches) >= limit:
                return matches

    return matches

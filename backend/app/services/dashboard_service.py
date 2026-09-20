from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models.alert import Alert
from app.models.article import Article
from app.models.article_business_impact import ArticleBusinessImpact
from app.models.article_sentiment import ArticleSentiment
from app.models.article_triage import ArticleTriage
from app.models.company import Company
from app.models.company_alias import CompanyAlias
from app.models.company_geography import CompanyGeography
from app.models.company_regulator import CompanyRegulator
from app.models.company_relationship import CompanyRelationship
from app.models.monitoring_topic import MonitoringTopic
from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight
from app.ingestion.sources import get_enabled_sources
from app.schemas.dashboard import (
    DashboardArticleItem,
    DashboardArticleResponse,
    DashboardCompaniesResponse,
    DashboardCompanyItem,
    DashboardCompanyRelationship,
    DashboardMonitoringTopic,
    RiskDrilldownResponse,
    DashboardIntelligenceItem,
    DashboardIntelligenceResponse,
    DashboardOverviewResponse,
    DashboardRiskAnalyticsResponse,
    DashboardRiskBucket,
)
from app.utils.article_metadata import publisher_name


async def get_dashboard_overview(
    db,
) -> DashboardOverviewResponse:
    now = datetime.now(
        timezone.utc
    )

    enabled_source_names = [
        source.name
        for source in get_enabled_sources()
    ]

    total_articles = await db.scalar(
        select(
            func.count(Article.id)
        ).where(
            Article.source_name.in_(
                enabled_source_names
            )
        )
    )

    processed_articles = await db.scalar(
        select(
            func.count(
                func.distinct(
                    ArticleTriage.article_id
                )
            )
        )
        .join(
            Company,
            Company.id
            == ArticleTriage.company_id,
        )
        .where(
            Company.is_active.is_(True)
        )
    )

    total_companies = await db.scalar(
        select(
            func.count(Company.id)
        )
        .where(
            Company.is_active.is_(True)
        )
    )

    high_risk_items = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            ),
            RiskAssessment.risk_level
            == "high",
        )
    )

    critical_risk_items = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            ),
            RiskAssessment.risk_level
            == "critical",
        )
    )

    from datetime import timedelta
    one_hour_ago = now - timedelta(hours=1)

    last_hour_articles = await db.scalar(
        select(func.count(Article.id)).where(
            Article.source_name.in_(enabled_source_names),
            Article.collected_at >= one_hour_ago,
        )
    )

    last_hour_processed = await db.scalar(
        select(
            func.count(func.distinct(ArticleTriage.article_id))
        )
        .join(Company, Company.id == ArticleTriage.company_id)
        .where(
            Company.is_active.is_(True),
            ArticleTriage.created_at >= one_hour_ago,
        )
    )

    return DashboardOverviewResponse(
        total_articles=total_articles or 0,
        processed_articles=processed_articles or 0,
        total_companies=total_companies or 0,
        high_risk_items=high_risk_items or 0,
        critical_risk_items=(critical_risk_items or 0),
        last_hour_articles=last_hour_articles or 0,
        last_hour_processed=last_hour_processed or 0,
    )


async def get_dashboard_articles(
    db,
    *,
    metric: str,
) -> DashboardArticleResponse:
    active_company_ids = select(Company.id).where(
        Company.is_active.is_(True)
    )

    columns = (
        Article.id.label("article_id"),
        Article.title,
        Article.source_name,
        Article.url,
        Article.published_at,
        Article.collected_at,
    )

    if metric == "total":
        statement = select(*columns).where(
            Article.source_name.in_(
                source.name
                for source in get_enabled_sources()
            )
        ).order_by(
            Article.published_at.desc().nullslast(),
            Article.id.desc(),
        )
        rows = (await db.execute(statement)).all()
        items = [
            DashboardArticleItem(
                **row._mapping,
                publisher_name=publisher_name(
                    row.source_name,
                    row.title,
                    row.url,
                ),
            )
            for row in rows
        ]
        return DashboardArticleResponse(count=len(items), items=items)

    if metric == "processed":
        statement = (
            select(
                *columns,
                ArticleTriage.event_type,
                ArticleSentiment.label.label("sentiment"),
                RiskAssessment.risk_level,
                RiskAssessment.risk_score,
                ArticleBusinessImpact.primary_category.label(
                    "business_impact"
                ),
            )
            .join(
                ArticleTriage,
                ArticleTriage.article_id == Article.id,
            )
            .outerjoin(
                ArticleSentiment,
                (
                    (ArticleSentiment.article_id == Article.id)
                    & (
                        ArticleSentiment.company_id
                        == ArticleTriage.company_id
                    )
                ),
            )
            .outerjoin(
                RiskAssessment,
                (
                    (RiskAssessment.article_id == Article.id)
                    & (
                        RiskAssessment.company_id
                        == ArticleTriage.company_id
                    )
                ),
            )
            .outerjoin(
                ArticleBusinessImpact,
                (
                    (ArticleBusinessImpact.article_id == Article.id)
                    & (
                        ArticleBusinessImpact.company_id
                        == ArticleTriage.company_id
                    )
                ),
            )
            .where(ArticleTriage.company_id.in_(active_company_ids))
            .distinct()
            .order_by(
                Article.published_at.desc().nullslast(),
                Article.id.desc(),
            )
        )
    elif metric in {"high-risk", "critical-risk"}:
        risk_level = metric.removesuffix("-risk")
        statement = (
            select(
                *columns,
                ArticleTriage.event_type,
                ArticleSentiment.label.label("sentiment"),
                RiskAssessment.risk_level,
                RiskAssessment.risk_score,
                ArticleBusinessImpact.primary_category.label(
                    "business_impact"
                ),
            )
            .join(
                RiskAssessment,
                RiskAssessment.article_id == Article.id,
            )
            .outerjoin(
                ArticleTriage,
                (
                    (ArticleTriage.article_id == Article.id)
                    & (
                        ArticleTriage.company_id
                        == RiskAssessment.company_id
                    )
                ),
            )
            .outerjoin(
                ArticleSentiment,
                (
                    (ArticleSentiment.article_id == Article.id)
                    & (
                        ArticleSentiment.company_id
                        == RiskAssessment.company_id
                    )
                ),
            )
            .outerjoin(
                ArticleBusinessImpact,
                (
                    (ArticleBusinessImpact.article_id == Article.id)
                    & (
                        ArticleBusinessImpact.company_id
                        == RiskAssessment.company_id
                    )
                ),
            )
            .where(
                RiskAssessment.company_id.in_(active_company_ids),
                RiskAssessment.risk_level == risk_level,
            )
            .order_by(
                RiskAssessment.risk_score.desc(),
                Article.published_at.desc().nullslast(),
                Article.id.desc(),
            )
        )
    else:
        raise ValueError(f"Unsupported dashboard article metric: {metric}")

    rows = (await db.execute(statement)).all()
    items = [
        DashboardArticleItem(
            **row._mapping,
            publisher_name=publisher_name(
                row.source_name,
                row.title,
                row.url,
            ),
        )
        for row in rows
    ]
    return DashboardArticleResponse(count=len(items), items=items)


async def get_dashboard_intelligence(
    db,
    *,
    limit: int = 20,
) -> DashboardIntelligenceResponse:
    query = (
        select(
            Article.id.label("article_id"),
            ArticleTriage.company_id.label(
                "company_id"
            ),
            ArticleTriage.company_name.label(
                "company_name"
            ),
            Article.title.label("title"),
            Article.source_name.label(
                "source_name"
            ),
            Article.url.label("url"),
            Article.published_at.label(
                "published_at"
            ),
            Article.collected_at.label(
                "collected_at"
            ),
            ArticleTriage.event_type.label(
                "event_type"
            ),
            ArticleTriage.urgency.label(
                "urgency"
            ),
            ArticleTriage.confidence.label(
                "confidence"
            ),
            ArticleTriage.summary.label(
                "summary"
            ),
            ArticleTriage.why_it_matters.label(
                "why_it_matters"
            ),
            RiskAssessment.risk_score.label(
                "risk_score"
            ),
            RiskAssessment.risk_level.label(
                "risk_level"
            ),
            RiskAssessment.escalation_action.label(
                "escalation_action"
            ),
            RiskAssessment.monitoring_topic.label(
                "monitoring_topic"
            ),
            RiskInsight.headline.label(
                "headline"
            ),
            RiskInsight.executive_summary.label(
                "executive_summary"
            ),
            RiskInsight.recommended_action.label(
                "recommended_action"
            ),
            RiskInsight.attention_level.label(
                "attention_level"
            ),
            RiskInsight.updated_at.label(
                "updated_at"
            ),
        )
        .join(
            ArticleTriage,
            ArticleTriage.article_id
            == Article.id,
        )
        .join(
            Company,
            Company.id
            == ArticleTriage.company_id,
        )
        .join(
            RiskAssessment,
            RiskAssessment.triage_id
            == ArticleTriage.id,
        )
        .join(
            RiskInsight,
            RiskInsight.risk_assessment_id
            == RiskAssessment.id,
        )
        .where(
            Company.is_active.is_(True)
        )
        .order_by(
            RiskInsight.updated_at.desc()
        )
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    items = [
        DashboardIntelligenceItem(
            **row,
            publisher_name=publisher_name(
                row["source_name"],
                row["title"],
                row["url"],
            ),
        )
        for row in rows
    ]

    return DashboardIntelligenceResponse(
        count=len(items),
        items=items,
    )


async def get_dashboard_risk_analytics(
    db,
) -> DashboardRiskAnalyticsResponse:
    total_assessments = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        )
        .where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            )
        )
    )

    average_risk_score = await db.scalar(
        select(
            func.avg(
                RiskAssessment.risk_score
            )
        )
        .where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            )
        )
    )

    highest_risk_score = await db.scalar(
        select(
            func.max(
                RiskAssessment.risk_score
            )
        )
        .where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            )
        )
    )

    human_review_count = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            ),
            RiskAssessment.requires_human_review
            .is_(True),
        )
    )

    immediate_alert_count = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            ),
            RiskAssessment.requires_immediate_alert
            .is_(True),
        )
    )

    risk_result = await db.execute(
        select(
            func.lower(RiskAssessment.risk_level).label("risk_level"),
            func.count(
                RiskAssessment.id
            ).label("count"),
        )
        .where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            )
        )
        .group_by(
            func.lower(RiskAssessment.risk_level)
        )
        .order_by(
            func.lower(RiskAssessment.risk_level)
        )
    )

    event_result = await db.execute(
        select(
            func.lower(RiskAssessment.event_type).label("event_type"),
            func.count(
                RiskAssessment.id
            ).label("count"),
        )
        .where(
            RiskAssessment.company_id.in_(
                select(Company.id).where(
                    Company.is_active.is_(True)
                )
            )
        )
        .group_by(
            func.lower(RiskAssessment.event_type)
        )
        .order_by(
            func.count(
                RiskAssessment.id
            ).desc()
        )
    )

    # risk_level is already lowercased via func.lower() in the query
    risk_dict = {(row.risk_level or ""): row.count for row in risk_result}
    standard_risks = ["critical", "high", "medium", "low"]
    risk_levels = []
    
    for r in standard_risks:
        if r in risk_dict:
            risk_levels.append(DashboardRiskBucket(label=r, count=risk_dict[r]))
            del risk_dict[r]
        elif r in ["high", "medium", "low"]:
            risk_levels.append(DashboardRiskBucket(label=r, count=0))
            
    for r, count in risk_dict.items():
        if r:
            risk_levels.append(DashboardRiskBucket(label=r, count=count))

    event_types = [
        DashboardRiskBucket(
            label=row.event_type,
            count=row.count,
        )
        for row in event_result
    ]

    return DashboardRiskAnalyticsResponse(
        total_assessments=(
            total_assessments or 0
        ),
        average_risk_score=float(
            average_risk_score or 0
        ),
        highest_risk_score=float(
            highest_risk_score or 0
        ),
        human_review_count=(
            human_review_count or 0
        ),
        immediate_alert_count=(
            immediate_alert_count or 0
        ),
        risk_levels=risk_levels,
        event_types=event_types,
    )


async def get_dashboard_companies(
    db,
) -> DashboardCompaniesResponse:
    company_result = await db.execute(
        select(Company)
        .where(
            Company.is_active.is_(True)
        )
        .order_by(
            Company.name.asc()
        )
    )

    companies = company_result.scalars().all()
    items = []

    for company in companies:
        alias_result = await db.execute(
            select(CompanyAlias.alias)
            .where(
                CompanyAlias.company_id
                == company.id
            )
            .order_by(
                CompanyAlias.alias.asc()
            )
        )

        geography_result = await db.execute(
            select(
                CompanyGeography.geography
            )
            .where(
                CompanyGeography.company_id
                == company.id
            )
            .order_by(
                CompanyGeography.geography.asc()
            )
        )

        regulator_result = await db.execute(
            select(
                CompanyRegulator.regulator
            )
            .where(
                CompanyRegulator.company_id
                == company.id
            )
            .order_by(
                CompanyRegulator.regulator.asc()
            )
        )

        relationship_result = await db.execute(
            select(CompanyRelationship)
            .where(
                CompanyRelationship.company_id
                == company.id
            )
            .order_by(
                CompanyRelationship.related_company_name.asc()
            )
        )

        topic_result = await db.execute(
            select(MonitoringTopic)
            .where(
                MonitoringTopic.company_id
                == company.id
            )
            .order_by(
                MonitoringTopic.priority.desc(),
                MonitoringTopic.topic.asc(),
            )
        )

        triage_count = await db.scalar(
            select(
                func.count(ArticleTriage.id)
            ).where(
                ArticleTriage.company_id
                == company.id
            )
        )

        risk_count = await db.scalar(
            select(
                func.count(
                    RiskAssessment.id
                )
            ).where(
                RiskAssessment.company_id
                == company.id
            )
        )

        high_risk_count = await db.scalar(
            select(
                func.count(
                    RiskAssessment.id
                )
            ).where(
                RiskAssessment.company_id
                == company.id,
                RiskAssessment.risk_level
                == "high",
            )
        )

        critical_risk_count = await db.scalar(
            select(
                func.count(
                    RiskAssessment.id
                )
            ).where(
                RiskAssessment.company_id
                == company.id,
                RiskAssessment.risk_level
                == "critical",
            )
        )

        alert_count = await db.scalar(
            select(
                func.count(Alert.id)
            ).where(
                Alert.company_id
                == company.id
            )
        )

        relationships = [
            DashboardCompanyRelationship(
                related_company_name=(
                    relationship.related_company_name
                ),
                relationship_type=(
                    relationship.relationship_type
                ),
            )
            for relationship
            in relationship_result.scalars().all()
        ]

        topics = [
            DashboardMonitoringTopic(
                topic=topic.topic,
                priority=topic.priority,
                is_active=topic.is_active,
            )
            for topic
            in topic_result.scalars().all()
        ]

        items.append(
            DashboardCompanyItem(
                id=company.id,
                name=company.name,
                website=company.website,
                industry=company.industry,
                is_active=company.is_active,
                aliases=list(
                    alias_result.scalars().all()
                ),
                geographies=list(
                    geography_result.scalars().all()
                ),
                regulators=list(
                    regulator_result.scalars().all()
                ),
                relationships=relationships,
                monitoring_topics=topics,
                triage_count=triage_count or 0,
                risk_assessment_count=(
                    risk_count or 0
                ),
                high_risk_count=(
                    high_risk_count or 0
                ),
                critical_risk_count=(
                    critical_risk_count or 0
                ),
                alert_count=alert_count or 0,
            )
        )

    return DashboardCompaniesResponse(
        count=len(items),
        items=items,
    )

async def get_dashboard_risk_analytics_drilldown(
    db,
    metric: str,
    value: str | None,
    page: int,
    page_size: int,
    search: str | None,
) -> RiskDrilldownResponse:
    from sqlalchemy import or_, desc
    
    # Base query for RiskAssessments of active companies
    stmt = select(RiskAssessment, Article).join(
        Article, RiskAssessment.article_id == Article.id
    ).where(
        RiskAssessment.company_id.in_(
            select(Company.id).where(Company.is_active.is_(True))
        )
    )

    if metric == "risk_level" and value:
        stmt = stmt.where(func.lower(RiskAssessment.risk_level) == value.lower())
    elif metric == "event_type" and value:
        stmt = stmt.where(func.lower(RiskAssessment.event_type) == value.lower())
    elif metric == "human_review":
        stmt = stmt.where(RiskAssessment.requires_human_review.is_(True))
    elif metric == "immediate_alert":
        stmt = stmt.where(RiskAssessment.requires_immediate_alert.is_(True))
    elif metric == "highest_risk_score":
        # Get max score
        max_score = await db.scalar(
            select(func.max(RiskAssessment.risk_score)).where(
                RiskAssessment.company_id.in_(
                    select(Company.id).where(Company.is_active.is_(True))
                )
            )
        )
        stmt = stmt.where(RiskAssessment.risk_score == max_score)
    elif metric == "average_risk_score" or metric == "total_assessments":
        pass # Includes all assessed articles

    if search:
        search_term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Article.title).like(search_term),
                func.lower(Article.source_name).like(search_term),
                func.lower(RiskAssessment.event_type).like(search_term),
            )
        )

    # Ordering: score descending, then published descending
    stmt = stmt.order_by(
        desc(RiskAssessment.risk_score),
        desc(Article.published_at)
    )

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt)

    # Pagination
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for risk, article in rows:
        items.append(
            DashboardArticleItem(
                article_id=article.id,
                title=article.title,
                source_name=article.source_name,
                url=article.url,
                published_at=article.published_at,
                publisher_name=article.source_name,
                collected_at=article.collected_at,
                event_type=risk.event_type,
                risk_level=risk.risk_level,
                risk_score=risk.risk_score,
            )
        )

    return RiskDrilldownResponse(
        metric=metric,
        value=value,
        total=total or 0,
        page=page,
        page_size=page_size,
        items=items,
    )

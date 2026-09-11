from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models.alert import Alert
from app.models.article import Article
from app.models.article_triage import ArticleTriage
from app.models.company import Company
from app.models.company_alias import CompanyAlias
from app.models.company_geography import CompanyGeography
from app.models.company_regulator import CompanyRegulator
from app.models.company_relationship import CompanyRelationship
from app.models.monitoring_topic import MonitoringTopic
from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight
from app.schemas.dashboard import (
    DashboardAlertItem,
    DashboardAlertsResponse,
    DashboardCompaniesResponse,
    DashboardCompanyItem,
    DashboardCompanyRelationship,
    DashboardMonitoringTopic,
    DashboardIntelligenceItem,
    DashboardIntelligenceResponse,
    DashboardOverviewResponse,
    DashboardRiskAnalyticsResponse,
    DashboardRiskBucket,
)


async def get_dashboard_overview(
    db,
) -> DashboardOverviewResponse:
    now = datetime.now(
        timezone.utc
    )

    total_articles = await db.scalar(
        select(
            func.count(Article.id)
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
    )

    total_companies = await db.scalar(
        select(
            func.count(Company.id)
        )
    )

    high_risk_items = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.risk_level
            == "high"
        )
    )

    critical_risk_items = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.risk_level
            == "critical"
        )
    )

    active_alerts = await db.scalar(
        select(
            func.count(Alert.id)
        ).where(
            Alert.delivered_at.is_(None)
        )
    )

    overdue_alerts = await db.scalar(
        select(
            func.count(Alert.id)
        ).where(
            Alert.delivered_at.is_(None),
            Alert.sla_due_at.is_not(None),
            Alert.sla_due_at < now,
        )
    )

    return DashboardOverviewResponse(
        total_articles=total_articles or 0,
        processed_articles=processed_articles or 0,
        total_companies=total_companies or 0,
        high_risk_items=high_risk_items or 0,
        critical_risk_items=(
            critical_risk_items or 0
        ),
        active_alerts=active_alerts or 0,
        overdue_alerts=overdue_alerts or 0,
    )


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
            RiskAssessment,
            RiskAssessment.triage_id
            == ArticleTriage.id,
        )
        .join(
            RiskInsight,
            RiskInsight.risk_assessment_id
            == RiskAssessment.id,
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
            **row
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
    )

    average_risk_score = await db.scalar(
        select(
            func.avg(
                RiskAssessment.risk_score
            )
        )
    )

    highest_risk_score = await db.scalar(
        select(
            func.max(
                RiskAssessment.risk_score
            )
        )
    )

    human_review_count = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.requires_human_review
            .is_(True)
        )
    )

    immediate_alert_count = await db.scalar(
        select(
            func.count(RiskAssessment.id)
        ).where(
            RiskAssessment.requires_immediate_alert
            .is_(True)
        )
    )

    risk_result = await db.execute(
        select(
            RiskAssessment.risk_level,
            func.count(
                RiskAssessment.id
            ).label("count"),
        )
        .group_by(
            RiskAssessment.risk_level
        )
        .order_by(
            RiskAssessment.risk_level
        )
    )

    event_result = await db.execute(
        select(
            RiskAssessment.event_type,
            func.count(
                RiskAssessment.id
            ).label("count"),
        )
        .group_by(
            RiskAssessment.event_type
        )
        .order_by(
            func.count(
                RiskAssessment.id
            ).desc()
        )
    )

    risk_levels = [
        DashboardRiskBucket(
            label=row.risk_level,
            count=row.count,
        )
        for row in risk_result
    ]

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


async def get_dashboard_alerts(
    db,
    *,
    limit: int = 50,
) -> DashboardAlertsResponse:
    now = datetime.now(
        timezone.utc
    )

    result = await db.execute(
        select(Alert)
        .order_by(
            Alert.created_at.desc()
        )
        .limit(limit)
    )

    records = result.scalars().all()

    items = []

    for alert in records:
        is_overdue = (
            alert.sla_due_at is not None
            and alert.delivered_at is None
            and alert.sla_due_at < now
        )

        items.append(
            DashboardAlertItem(
                id=alert.id,
                article_id=alert.article_id,
                company_id=alert.company_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                delivery_status=(
                    alert.delivery_status
                ),
                delivery_channel=(
                    alert.delivery_channel
                ),
                retry_count=alert.retry_count,
                last_error=alert.last_error,
                requires_immediate_delivery=(
                    alert.requires_immediate_delivery
                ),
                sla_due_at=alert.sla_due_at,
                delivered_at=alert.delivered_at,
                is_overdue=is_overdue,
                created_at=alert.created_at,
                updated_at=alert.updated_at,
            )
        )

    total_alerts = len(items)

    active_alerts = sum(
        1
        for item in items
        if item.delivered_at is None
    )

    delivered_alerts = sum(
        1
        for item in items
        if item.delivery_status
        == "delivered"
    )

    failed_alerts = sum(
        1
        for item in items
        if item.delivery_status
        == "failed"
    )

    overdue_alerts = sum(
        1
        for item in items
        if item.is_overdue
    )

    return DashboardAlertsResponse(
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        delivered_alerts=delivered_alerts,
        failed_alerts=failed_alerts,
        overdue_alerts=overdue_alerts,
        items=items,
    )


async def get_dashboard_companies(
    db,
) -> DashboardCompaniesResponse:
    company_result = await db.execute(
        select(Company)
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

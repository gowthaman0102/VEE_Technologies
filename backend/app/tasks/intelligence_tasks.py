import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.services.alert_service import (
    create_alert_for_intelligence,
)
from app.services.event_cluster_assignment_service import (
    assign_article_to_event_cluster,
)
from app.services.article_sentiment_service import (
    analyze_article_sentiment,
)
from app.services.article_business_impact_service import (
    analyze_article_business_impact,
)
from app.services.article_competitor_analysis_service import (
    analyze_article_competitors,
)
from app.services.article_triage_service import (
    triage_article,
)
from app.services.risk_insight_service import (
    generate_risk_insight,
)
from app.services.client_configuration_service import get_client_config


async def _process_article_intelligence(
    *,
    article_id: int,
    company_id: int,
) -> dict:
    async with CeleryAsyncSessionLocal() as db:
        features = {
            "event_clustering_enabled": True,
            "sentiment_enabled": True,
            "business_impact_enabled": True,
            "competitor_detection_enabled": True,
            "alerts_enabled": True,
        }
        if isinstance(db, AsyncSession):
            config = await get_client_config(db, company_id)
            features.update(config.features.model_dump())

        cluster_result = None
        if features["event_clustering_enabled"]:
            cluster_result = await assign_article_to_event_cluster(
                db,
                article_id=article_id,
                company_id=company_id,
            )

        sentiment_result = None
        if features["sentiment_enabled"]:
            sentiment_result = await analyze_article_sentiment(
                db,
                article_id=article_id,
                company_id=company_id,
            )

        business_impact_result = None
        if features["business_impact_enabled"]:
            business_impact_result = await analyze_article_business_impact(
                db,
                article_id=article_id,
                company_id=company_id,
            )

        competitor_result = None
        if features["competitor_detection_enabled"]:
            competitor_result = await analyze_article_competitors(
                db,
                article_id=article_id,
                company_id=company_id,
            )

        triage_result = await triage_article(
            db,
            article_id=article_id,
            company_id=company_id,
        )

        result = await generate_risk_insight(
            db,
            article_id=article_id,
            company_id=company_id,
        )

        alert_result = None
        if features["alerts_enabled"]:
            alert_result = await create_alert_for_intelligence(
                db,
                article_id=article_id,
                company_id=company_id,
            )
        alert = alert_result.alert if alert_result is not None else None

        return {
            "article_id": result.article_id,
            "company_id": result.company_id,
            "event_cluster_id": (
                cluster_result.cluster_id
                if cluster_result is not None
                else None
            ),
            "event_cluster_created": (
                cluster_result.created_new_cluster
                if cluster_result is not None
                else False
            ),
            "event_cluster_similarity": (
                cluster_result.similarity
                if cluster_result is not None
                else None
            ),
            "sentiment_label": (
                sentiment_result.sentiment.label
                if sentiment_result is not None
                else None
            ),
            "sentiment_score": (
                sentiment_result.sentiment.score
                if sentiment_result is not None
                else None
            ),
            "sentiment_reason": (
                sentiment_result.sentiment.reason
                if sentiment_result is not None
                else None
            ),
            "sentiment_model": (
                sentiment_result.sentiment.model
                if sentiment_result is not None
                else None
            ),
            "business_impact_primary": (
                business_impact_result
                .impact
                .primary_category
                if business_impact_result is not None
                else None
            ),
            "business_impact_categories": (
                business_impact_result
                .impact
                .categories
                if business_impact_result is not None
                else []
            ),
            "business_impact_summary": (
                business_impact_result
                .impact
                .impact_summary
                if business_impact_result is not None
                else None
            ),
            "business_impact_model": (
                business_impact_result
                .impact
                .model
                if business_impact_result is not None
                else None
            ),
            "competitors": (
                competitor_result.competitors
                if competitor_result is not None
                else []
            ),
            "competitor_count": len(competitor_result.competitors) if competitor_result is not None else 0,
            "triage_event_type": (
                triage_result.triage.event_type
            ),
            "triage_urgency": (
                triage_result.triage.urgency
            ),
            "triage_confidence": (
                triage_result.triage.confidence
            ),
            "model": result.model,
            "risk_score": (
                result.assessment.risk.risk_score
            ),
            "risk_level": (
                result.assessment.risk.risk_level
            ),
            "escalation_action": (
                result.assessment.escalation.action
            ),
            "attention_level": (
                result.insight.attention_level
            ),
            "headline": (
                result.insight.headline
            ),
            "alert_created": (
                alert_result.should_create_alert
                if alert_result is not None
                else False
            ),
            "alert_id": (
                alert.id
                if alert is not None
                else None
            ),
            "alert_type": (
                alert.alert_type
                if alert is not None
                else None
            ),
            "alert_severity": (
                alert.severity
                if alert is not None
                else None
            ),
            "alert_status": (
                alert.delivery_status
                if alert is not None
                else None
            ),
            "alert_sla_due_at": (
                alert.sla_due_at.isoformat()
                if (
                    alert is not None
                    and alert.sla_due_at is not None
                )
                else None
            ),
        }


@celery_app.task(
    bind=True,
    name="intelligence.process_article",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def process_article_intelligence_task(
    self,
    article_id: int,
    company_id: int,
) -> dict:
    return asyncio.run(
        _process_article_intelligence(
            article_id=article_id,
            company_id=company_id,
        )
    )

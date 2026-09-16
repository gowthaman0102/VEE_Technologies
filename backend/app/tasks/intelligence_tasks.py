import asyncio

from app.core.celery_app import celery_app
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.services.alert_service import (
    create_alert_for_intelligence,
)
from app.services.article_sentiment_service import (
    analyze_article_sentiment,
)
from app.services.article_triage_service import (
    triage_article,
)
from app.services.risk_insight_service import (
    generate_risk_insight,
)


async def _process_article_intelligence(
    *,
    article_id: int,
    company_id: int,
) -> dict:
    async with CeleryAsyncSessionLocal() as db:
        sentiment_result = (
            await analyze_article_sentiment(
                db,
                article_id=article_id,
                company_id=company_id,
            )
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

        alert_result = (
            await create_alert_for_intelligence(
                db,
                article_id=article_id,
                company_id=company_id,
            )
        )

        alert = alert_result.alert

        return {
            "article_id": result.article_id,
            "company_id": result.company_id,
            "sentiment_label": (
                sentiment_result.sentiment.label
            ),
            "sentiment_score": (
                sentiment_result.sentiment.score
            ),
            "sentiment_reason": (
                sentiment_result.sentiment.reason
            ),
            "sentiment_model": (
                sentiment_result.sentiment.model
            ),
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

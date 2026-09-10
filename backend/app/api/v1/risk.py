from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.risk_assessment_api import (
    EscalationResponse,
    MonitoringPriorityResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskCalculationResponse,
    StoredRiskAssessmentResponse,
)
from app.services.risk_assessment_read_service import (
    get_risk_assessment,
)
from app.services.risk_assessment_service import (
    StoredTriageNotFoundError,
    assess_article_risk,
)


router = APIRouter(
    prefix="/risk",
    tags=["risk"],
)


@router.post(
    "/articles/{article_id}",
    response_model=RiskAssessmentResponse,
)
async def run_risk_assessment(
    article_id: int,
    payload: RiskAssessmentRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await assess_article_risk(
            db,
            article_id=article_id,
            company_id=payload.company_id,
        )
    except StoredTriageNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return RiskAssessmentResponse(
        article_id=result.article_id,
        company_id=result.company_id,
        company_name=result.company_name,
        event_type=result.event_type,
        urgency=result.urgency,
        confidence=result.confidence,
        monitoring_priority=MonitoringPriorityResponse(
            monitoring_topic=(
                result.monitoring_priority.monitoring_topic
            ),
            priority=result.monitoring_priority.priority,
            source=result.monitoring_priority.source,
        ),
        risk=RiskCalculationResponse(
            priority_score=result.risk.priority_score,
            urgency_score=result.risk.urgency_score,
            confidence_score=result.risk.confidence_score,
            risk_score=result.risk.risk_score,
            risk_level=result.risk.risk_level,
        ),
        escalation=EscalationResponse(
            action=result.escalation.action,
            requires_human_review=(
                result.escalation.requires_human_review
            ),
            requires_immediate_alert=(
                result.escalation.requires_immediate_alert
            ),
        ),
    )


@router.get(
    "/articles/{article_id}",
    response_model=StoredRiskAssessmentResponse,
)
async def read_risk_assessment(
    article_id: int,
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    record = await get_risk_assessment(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored risk assessment not found.",
        )

    return StoredRiskAssessmentResponse(
        id=record.id,
        triage_id=record.triage_id,
        article_id=record.article_id,
        company_id=record.company_id,
        event_type=record.event_type,
        monitoring_topic=record.monitoring_topic,
        topic_priority=record.topic_priority,
        priority_source=record.priority_source,
        urgency=record.urgency,
        confidence=record.confidence,
        risk_score=record.risk_score,
        risk_level=record.risk_level,
        escalation_action=record.escalation_action,
        requires_human_review=(
            record.requires_human_review
        ),
        requires_immediate_alert=(
            record.requires_immediate_alert
        ),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )

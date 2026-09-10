from datetime import datetime

from pydantic import BaseModel, Field


class RiskAssessmentRequest(BaseModel):
    company_id: int = Field(ge=1)


class MonitoringPriorityResponse(BaseModel):
    monitoring_topic: str | None
    priority: str
    source: str


class RiskCalculationResponse(BaseModel):
    priority_score: float
    urgency_score: float
    confidence_score: float
    risk_score: float
    risk_level: str


class EscalationResponse(BaseModel):
    action: str
    requires_human_review: bool
    requires_immediate_alert: bool


class RiskAssessmentResponse(BaseModel):
    article_id: int
    company_id: int
    company_name: str
    event_type: str
    urgency: str
    confidence: float
    monitoring_priority: MonitoringPriorityResponse
    risk: RiskCalculationResponse
    escalation: EscalationResponse


class StoredRiskAssessmentResponse(BaseModel):
    id: int
    triage_id: int
    article_id: int
    company_id: int
    event_type: str
    monitoring_topic: str | None
    topic_priority: str
    priority_source: str
    urgency: str
    confidence: float
    risk_score: float
    risk_level: str
    escalation_action: str
    requires_human_review: bool
    requires_immediate_alert: bool
    created_at: datetime
    updated_at: datetime

from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    total_articles: int
    processed_articles: int
    total_companies: int
    high_risk_items: int
    critical_risk_items: int
    active_alerts: int
    overdue_alerts: int

from datetime import datetime


class DashboardIntelligenceItem(BaseModel):
    article_id: int
    company_id: int
    company_name: str

    title: str
    source_name: str
    url: str
    published_at: datetime | None

    event_type: str
    urgency: str
    confidence: float

    summary: str
    why_it_matters: str

    risk_score: float
    risk_level: str
    escalation_action: str
    monitoring_topic: str | None

    headline: str
    executive_summary: str
    recommended_action: str
    attention_level: str

    updated_at: datetime


class DashboardIntelligenceResponse(BaseModel):
    count: int
    items: list[DashboardIntelligenceItem]


class DashboardRiskBucket(BaseModel):
    label: str
    count: int


class DashboardRiskAnalyticsResponse(BaseModel):
    total_assessments: int
    average_risk_score: float
    highest_risk_score: float
    human_review_count: int
    immediate_alert_count: int
    risk_levels: list[DashboardRiskBucket]
    event_types: list[DashboardRiskBucket]


class DashboardAlertItem(BaseModel):
    id: int
    article_id: int
    company_id: int

    alert_type: str
    severity: str
    title: str
    message: str

    delivery_status: str
    delivery_channel: str | None
    retry_count: int
    last_error: str | None

    requires_immediate_delivery: bool
    sla_due_at: datetime | None
    delivered_at: datetime | None

    is_overdue: bool

    created_at: datetime
    updated_at: datetime


class DashboardAlertsResponse(BaseModel):
    total_alerts: int
    active_alerts: int
    delivered_alerts: int
    failed_alerts: int
    overdue_alerts: int
    items: list[DashboardAlertItem]


class DashboardMonitoringTopic(BaseModel):
    topic: str
    priority: str
    is_active: bool


class DashboardCompanyRelationship(BaseModel):
    related_company_name: str
    relationship_type: str


class DashboardCompanyItem(BaseModel):
    id: int
    name: str
    website: str | None
    industry: str | None
    is_active: bool

    aliases: list[str]
    geographies: list[str]
    regulators: list[str]
    relationships: list[DashboardCompanyRelationship]
    monitoring_topics: list[DashboardMonitoringTopic]

    triage_count: int
    risk_assessment_count: int
    high_risk_count: int
    critical_risk_count: int
    alert_count: int


class DashboardCompaniesResponse(BaseModel):
    count: int
    items: list[DashboardCompanyItem]

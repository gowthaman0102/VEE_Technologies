from pydantic import BaseModel
from datetime import datetime


class DashboardOverviewResponse(BaseModel):
    total_articles: int
    processed_articles: int
    total_companies: int
    high_risk_items: int
    critical_risk_items: int
    last_hour_articles: int = 0
    last_hour_processed: int = 0


class DashboardArticleItem(BaseModel):
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None
    publisher_name: str
    collected_at: datetime
    event_type: str | None = None
    sentiment: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None
    collected_at: datetime


class DashboardArticleResponse(BaseModel):
    count: int
    items: list[DashboardArticleItem]

from datetime import datetime


class DashboardIntelligenceItem(BaseModel):
    article_id: int
    company_id: int
    company_name: str

    title: str
    source_name: str
    url: str
    published_at: datetime | None
    publisher_name: str

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

    sentiment: str | None = None

    updated_at: datetime
    collected_at: datetime


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


class RiskDrilldownResponse(BaseModel):
    metric: str
    value: str | None = None
    total: int
    page: int
    page_size: int
    items: list[DashboardArticleItem]


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

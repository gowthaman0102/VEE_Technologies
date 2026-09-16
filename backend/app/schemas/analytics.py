from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleTrendPoint(BaseModel):
    bucket: str | None
    article_count: int = 0


class ArticleTrendResponse(BaseModel):
    company_id: int
    bucket: str
    points: list[ArticleTrendPoint]


class SentimentTrendResponse(BaseModel):
    company_id: int
    positive: int = 0
    neutral: int = 0
    negative: int = 0


class RiskTrendResponse(BaseModel):
    company_id: int
    average_risk_score: float = 0.0
    highest_risk_score: float = 0.0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0


class BusinessImpactResponse(BaseModel):
    company_id: int
    items: dict[str, int] = Field(default_factory=dict)


class EventAnalyticsResponse(BaseModel):
    company_id: int
    total_events: int = 0
    largest_events: list[dict] = Field(default_factory=list)


class SourceAnalyticsResponse(BaseModel):
    company_id: int
    sources: list[dict] = Field(default_factory=list)


class CompetitorAnalyticsResponse(BaseModel):
    company_id: int
    competitors: list[dict] = Field(default_factory=list)


class AnalyticsOverviewResponse(BaseModel):
    company_id: int
    start: datetime
    end: datetime
    total_articles: int = 0
    total_events: int = 0
    sentiment: dict[str, int] = Field(default_factory=dict)
    risk: dict[str, float | int] = Field(default_factory=dict)
    business_impact: dict[str, int] = Field(default_factory=dict)
    competitors: list[dict] = Field(default_factory=list)

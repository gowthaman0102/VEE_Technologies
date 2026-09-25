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
    summary: dict[str, int] = Field(default_factory=lambda: {"positive": 0, "neutral": 0, "negative": 0})
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    series: list[dict] = Field(default_factory=list)


class RiskTrendResponse(BaseModel):
    company_id: int
    summary: dict[str, float | int] = Field(default_factory=lambda: {
        "average_risk_score": 0.0,
        "highest_risk_score": 0.0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
    })
    average_risk_score: float = 0.0
    highest_risk_score: float = 0.0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    series: list[dict] = Field(default_factory=list)


class BusinessImpactResponse(BaseModel):
    company_id: int
    items: dict[str, int] = Field(default_factory=dict)
    primary_distribution: dict[str, int] = Field(
        default_factory=dict
    )
    category_distribution: dict[str, int] = Field(
        default_factory=dict
    )
    series: list[dict] = Field(default_factory=list)
    category_series: list[dict] = Field(default_factory=list)


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

class PublisherCountryItem(BaseModel):
    country_code: str | None
    country_name: str | None
    article_count: int

class PublisherCountryDistributionResponse(BaseModel):
    company_id: int
    distribution: list[PublisherCountryItem] = Field(default_factory=list)

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
    comparison: dict[str, float | int] = Field(default_factory=dict)
    publisher_country_distribution: list[PublisherCountryItem] = Field(default_factory=list)

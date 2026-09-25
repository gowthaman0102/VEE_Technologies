from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


REPORT_SECTIONS = {
    "executive_summary",
    "kpis",
    "articles",
    "sentiment",
    "risk",
    "business_impact",
    "events",
    "sources",
    "competitors",
    "alerts",
}
FEATURE_KEYS = {
    "sentiment_enabled",
    "risk_enabled",
    "business_impact_enabled",
    "competitor_detection_enabled",
    "event_clustering_enabled",
    "alerts_enabled",
    "reports_enabled",
    "publisher_country_enabled",
}


class SourceConfiguration(BaseModel):
    google_news_enabled: bool = True
    newsapi_enabled: bool = True
    official_sources: list[str] = Field(default_factory=list)
    preferred_sources: list[str] = Field(default_factory=list)
    excluded_sources: list[str] = Field(default_factory=list)


class RiskConfiguration(BaseModel):
    medium_threshold: int = Field(default=40, ge=0, le=100)
    high_threshold: int = Field(default=60, ge=0, le=100)
    critical_threshold: int = Field(default=80, ge=0, le=100)

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "RiskConfiguration":
        if not self.medium_threshold < self.high_threshold < self.critical_threshold:
            raise ValueError("risk thresholds must satisfy medium < high < critical")
        return self


class AlertConfiguration(BaseModel):
    enabled: bool = True
    minimum_risk_level: Literal["low", "medium", "high", "critical"] = "high"
    immediate_alert_level: Literal["low", "medium", "high", "critical"] = "critical"
    sla_minutes: int = Field(default=60, gt=0)
    enabled_channels: list[str] = Field(default_factory=list)


class ReportConfiguration(BaseModel):
    enabled_sections: list[str] = Field(
        default_factory=lambda: sorted(REPORT_SECTIONS)
    )
    top_article_limit: int = Field(default=20, gt=0)
    highest_risk_limit: int = Field(default=10, gt=0)
    report_title_template: str = "{company_name} Media Intelligence Report"

    @model_validator(mode="after")
    def validate_sections(self) -> "ReportConfiguration":
        unknown = set(self.enabled_sections) - REPORT_SECTIONS
        if unknown:
            raise ValueError(f"unknown report sections: {sorted(unknown)}")
        return self


class FeatureConfiguration(BaseModel):
    sentiment_enabled: bool = True
    risk_enabled: bool = True
    business_impact_enabled: bool = True
    competitor_detection_enabled: bool = True
    event_clustering_enabled: bool = True
    alerts_enabled: bool = True
    reports_enabled: bool = True
    publisher_country_enabled: bool = True


class BrandingConfiguration(BaseModel):
    display_name: str | None = None
    logo_reference: str | None = None
    primary_accent: str | None = None
    report_header_name: str | None = None


class ClientConfiguration(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    company_name: str
    aliases: list[str] = Field(default_factory=list)
    monitoring_topics: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    regulators: list[str] = Field(default_factory=list)
    sources: SourceConfiguration
    risk: RiskConfiguration
    alerts: AlertConfiguration
    reports: ReportConfiguration
    features: FeatureConfiguration
    branding: BrandingConfiguration


class ClientConfigurationUpdate(BaseModel):
    sources: SourceConfiguration | None = None
    risk: RiskConfiguration | None = None
    alerts: AlertConfiguration | None = None
    reports: ReportConfiguration | None = None
    features: FeatureConfiguration | None = None
    branding: BrandingConfiguration | None = None

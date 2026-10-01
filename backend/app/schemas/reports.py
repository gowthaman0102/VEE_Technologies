from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    company_id: int = Field(gt=0)
    report_type: Literal[
        "daily",
        "weekly",
        "monthly",
        "custom",
        "all_history",
    ] = "custom"
    report_template: Literal["executive", "detailed", "board_ready"] = "detailed"
    
    report_scope: Literal[
        "standard", 
        "search_results", 
        "business_impact",
        "analytics_snapshot",
        "intelligence_export",
    ] = "standard"
    
    article_ids: list[int] | None = None
    
    business_impact_category: Literal[
        "financial",
        "operational",
        "legal",
        "regulatory",
        "cybersecurity",
        "reputation",
        "customer",
        "product",
        "market",
        "competitive"
    ] | None = None
    
    search_query: str | None = None
    search_mode: Literal['keyword', 'semantic'] | None = None  
    search_filters: dict | None = None
    minimum_similarity: float | None = None
    
    start_date: datetime | None = None
    end_date: datetime | None = None
    time_mode: Literal["media", "ingestion"] = "media"
    include_details: bool = True
    scope_metadata: dict | None = None

class ReportMetric(BaseModel):
    label: str
    value: float | int


class ReportRow(BaseModel):
    metric: str
    value: str


class ReportSummaryResponse(BaseModel):
    company_id: int
    start_date: datetime
    end_date: datetime
    total_articles: int
    total_events: int
    critical_risk_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    sentiment_balance: dict[str, int]
    metrics: list[ReportMetric]


class ReportHistoryItem(BaseModel):
    id: int
    company_id: int
    report_type: str
    report_template: str = "detailed"
    report_scope: str | None = None
    scope_metadata: dict | None = None
    file_format: str
    filename: str | None
    content_type: str | None
    period_start: datetime
    period_end: datetime
    status: str
    generated_at: datetime | None
    error: str | None
    created_at: datetime | None = None


class ReportBatchHistoryItem(BaseModel):
    batch_id: str
    id: int | None = None  # primary record id, for solo-batches
    company_id: int
    report_type: str
    report_template: str = "detailed"
    report_scope: str | None = None
    scope_metadata: dict | None = None
    period_start: datetime
    period_end: datetime
    status: str
    generated_at: datetime | None
    error: str | None
    formats: dict[str, ReportHistoryItem]


class ReportHistoryResponse(BaseModel):
    count: int
    items: list[ReportBatchHistoryItem]

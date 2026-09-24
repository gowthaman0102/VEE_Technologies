from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    company_id: int = Field(gt=0)
    report_type: str = Field(default="custom", min_length=1, max_length=50)
    start_date: datetime | None = None
    end_date: datetime | None = None
    time_mode: Literal["media", "ingestion"] = "media"
    include_details: bool = True
    article_ids: list[int] | None = Field(default=None, min_length=1)
    report_scope: Literal["standard", "search", "analytics"] = "standard"
    report_title: str | None = Field(default=None, max_length=200)


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
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    sentiment_balance: dict[str, int]
    metrics: list[ReportMetric]


class ReportHistoryItem(BaseModel):
    id: int
    company_id: int
    report_type: str
    file_format: str
    filename: str | None
    content_type: str | None
    period_start: datetime
    period_end: datetime
    status: str
    generated_at: datetime | None
    error: str | None
    created_at: datetime


class ReportBatchHistoryItem(BaseModel):
    batch_id: str
    company_id: int
    report_type: str
    period_start: datetime
    period_end: datetime
    status: str
    generated_at: datetime | None
    error: str | None
    formats: dict[str, ReportHistoryItem]


class ReportHistoryResponse(BaseModel):
    count: int
    items: list[ReportBatchHistoryItem]

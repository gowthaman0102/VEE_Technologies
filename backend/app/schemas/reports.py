from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    company_id: int = Field(gt=0)
    start_date: datetime
    end_date: datetime
    format: Literal["pdf", "xlsx", "csv"] = "pdf"
    include_details: bool = True


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
    filename: str
    content_type: str
    period_start: datetime
    period_end: datetime
    created_at: datetime


class ReportHistoryResponse(BaseModel):
    count: int
    items: list[ReportHistoryItem]

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    company_id: int = Field(gt=0)
    start_date: str = Field(min_length=1)
    end_date: str = Field(min_length=1)
    include_details: bool = True


class ReportMetric(BaseModel):
    label: str
    value: float | int


class ReportRow(BaseModel):
    metric: str
    value: str


class ReportSummaryResponse(BaseModel):
    company_id: int
    start_date: str
    end_date: str
    total_articles: int
    total_events: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    sentiment_balance: dict[str, int]
    metrics: list[ReportMetric]


class ReportExportResponse(BaseModel):
    company_id: int
    format: str
    filename: str
    content_type: str
    rows: list[ReportRow]

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ReportType = Literal["daily", "weekly", "monthly", "custom"]
ReportTemplate = Literal["executive", "detailed", "board_ready"]
ReportScope = Literal["standard", "business_impact"]
ReportFormat = Literal["pdf", "xlsx", "csv"]


class ReportSchedulePayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    report_type: ReportType
    time_mode: Literal["media", "ingestion"] = "media"
    report_scope: ReportScope = "standard"
    business_impact_category: Literal[
        "financial", "operational", "legal", "regulatory", "cybersecurity",
        "reputation", "customer", "product", "market", "competitive",
    ] | None = None
    report_template: ReportTemplate = "detailed"
    formats: list[ReportFormat] = Field(default_factory=lambda: ["pdf", "xlsx", "csv"], min_length=1, max_length=3)
    run_time_utc: str = Field(default="09:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    day_of_week: int = Field(default=0, ge=0, le=6)
    day_of_month: int = Field(default=1, ge=1, le=28)
    custom_period_days: int = Field(default=7, ge=1, le=365)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Schedule name must not be blank.")
        return normalized

    @field_validator("formats")
    @classmethod
    def require_unique_formats(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Report formats must be unique.")
        return value

    @model_validator(mode="after")
    def validate_scope(self) -> "ReportSchedulePayload":
        if self.report_scope == "business_impact" and self.business_impact_category is None:
            raise ValueError("business_impact_category is required for business impact schedules.")
        if self.report_scope == "standard":
            self.business_impact_category = None
        return self


class ReportScheduleResponse(ReportSchedulePayload):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None
    next_run_at: datetime


class ReportScheduleListResponse(BaseModel):
    count: int
    items: list[ReportScheduleResponse]


class ReportRecipientsUpdate(BaseModel):
    emails: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("emails")
    @classmethod
    def normalize_and_validate_emails(cls, values: list[str]) -> list[str]:
        normalized = sorted({value.strip().lower() for value in values})
        if any(len(value) > 320 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) for value in normalized):
            raise ValueError("Every recipient must be a valid email address.")
        return normalized


class ReportRecipientsResponse(BaseModel):
    count: int
    emails: list[str]
    delivery_configured: bool
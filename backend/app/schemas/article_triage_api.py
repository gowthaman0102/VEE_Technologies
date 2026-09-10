from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.article_triage import ArticleTriageResult


class ArticleTriageRequest(BaseModel):
    company_id: int = Field(ge=1)


class ArticleTriageResponse(BaseModel):
    article_id: int
    model: str
    triage: ArticleTriageResult


class StoredArticleTriageResponse(BaseModel):
    id: int
    article_id: int
    company_id: int
    company_name: str
    event_type: str
    summary: str
    why_it_matters: str
    evidence: list[str]
    potential_impact: str
    urgency: str
    confidence: float
    llm_model: str
    created_at: datetime
    updated_at: datetime


class ArticleTriageBatchRequest(BaseModel):
    company_id: int = Field(ge=1)
    article_ids: list[int] = Field(
        min_length=1,
    )
    rag_limit: int = Field(
        default=3,
        ge=1,
        le=10,
    )


class ArticleTriageBatchItemResponse(BaseModel):
    article_id: int
    status: Literal[
        "success",
        "not_found",
        "failed",
    ]
    model: str | None = None
    triage: ArticleTriageResult | None = None
    error: str | None = None


class ArticleTriageBatchResponse(BaseModel):
    company_id: int
    requested_count: int
    success_count: int
    not_found_count: int
    failed_count: int
    items: list[ArticleTriageBatchItemResponse]

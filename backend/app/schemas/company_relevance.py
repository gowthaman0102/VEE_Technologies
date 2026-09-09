from datetime import datetime

from pydantic import BaseModel, Field


class CompanySemanticRelevanceRequest(BaseModel):
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
    )

    threshold: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )


class ArticleRelevanceResponse(BaseModel):
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None = None
    distance: float
    similarity: float
    is_relevant: bool


class CompanySemanticRelevanceResponse(BaseModel):
    company_id: int
    company_name: str
    threshold: float
    context_text: str
    count: int
    relevant_count: int
    results: list[
        ArticleRelevanceResponse
    ]

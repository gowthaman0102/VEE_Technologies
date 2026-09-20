from datetime import datetime

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000,
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    minimum_similarity: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )


class SemanticSearchResultResponse(BaseModel):
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None = None
    distance: float
    similarity: float
    event_type: str | None = None
    sentiment: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None
    event_cluster_id: int | None = None
    publisher_name: str = ""
    collected_at: datetime | None = None


class SemanticSearchResponse(BaseModel):
    query: str
    count: int
    results: list[
        SemanticSearchResultResponse
    ]

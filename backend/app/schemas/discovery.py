from datetime import datetime

from pydantic import BaseModel


class KeywordSearchResult(BaseModel):
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None
    publisher_name: str = ""
    event_type: str | None = None
    sentiment: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None
    event_cluster_id: int | None = None
    collected_at: datetime | None = None


class KeywordSearchResponse(BaseModel):
    query: str
    count: int
    results: list[KeywordSearchResult]

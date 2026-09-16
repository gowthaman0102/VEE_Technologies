from datetime import datetime

from pydantic import BaseModel


class KeywordSearchResult(BaseModel):
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None


class KeywordSearchResponse(BaseModel):
    query: str
    count: int
    results: list[KeywordSearchResult]


class EventClusterItem(BaseModel):
    id: int
    company_id: int
    title: str | None
    representative_article_id: int | None
    first_published_at: datetime | None
    last_published_at: datetime | None
    article_count: int


class EventClusterResponse(BaseModel):
    count: int
    items: list[EventClusterItem]

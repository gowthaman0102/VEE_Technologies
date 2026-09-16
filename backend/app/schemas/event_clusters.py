from datetime import datetime

from pydantic import BaseModel


class EventMember(BaseModel):
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: datetime | None
    similarity: float | None


class EventClusterDetailResponse(BaseModel):
    id: int
    company_id: int
    title: str | None
    representative_article_id: int | None
    first_published_at: datetime | None
    last_published_at: datetime | None
    members: list[EventMember]

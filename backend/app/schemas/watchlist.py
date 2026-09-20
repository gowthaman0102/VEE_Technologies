from pydantic import BaseModel, ConfigDict, Field


class WatchlistItemCreate(BaseModel):
    company_id: int = Field(gt=0)
    item_type: str = Field(min_length=1, max_length=50)
    item_name: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=500)


class WatchlistItemUpdate(BaseModel):
    item_type: str | None = Field(default=None, min_length=1, max_length=50)
    item_name: str | None = Field(default=None, min_length=1, max_length=200)
    value: str | None = Field(default=None, min_length=1, max_length=500)
    is_active: bool | None = None


class WatchlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    item_type: str
    item_name: str
    value: str
    is_active: bool


class WatchlistListResponse(BaseModel):
    count: int
    items: list[WatchlistItemResponse]


class WatchlistMatchResponse(BaseModel):
    watchlist_item_id: int
    item_type: str
    item_name: str
    value: str
    article_id: int
    title: str
    source_name: str
    url: str
    published_at: str | None = None
    event_type: str | None = None
    monitoring_topic: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    business_impact: str | None = None
    publisher_name: str
    collected_at: str


class WatchlistMatchListResponse(BaseModel):
    count: int
    matches: list[WatchlistMatchResponse]


class WatchlistDeleteResponse(BaseModel):
    deleted: bool

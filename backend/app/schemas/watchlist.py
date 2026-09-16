from pydantic import BaseModel, ConfigDict, Field


class WatchlistItemCreate(BaseModel):
    company_id: int = Field(gt=0)
    item_type: str = Field(min_length=1, max_length=50)
    item_name: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=500)


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


class WatchlistDeleteResponse(BaseModel):
    deleted: bool

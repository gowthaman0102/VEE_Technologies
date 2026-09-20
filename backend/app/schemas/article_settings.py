from pydantic import BaseModel, ConfigDict, Field


class ArticleCategoryCreate(BaseModel):
    company_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    priority: str = Field(default="medium", min_length=1, max_length=20)


class ArticleCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    priority: str | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None


class ArticleCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    description: str | None = None
    priority: str
    is_active: bool


class ArticleCategoryListResponse(BaseModel):
    count: int
    items: list[ArticleCategoryResponse]


class ArticleCategoryDeleteResponse(BaseModel):
    deleted: bool

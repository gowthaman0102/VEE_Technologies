from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleCreate(BaseModel):
    company_id: int | None = Field(default=None, gt=0)
    source_name: str = Field(min_length=1, max_length=200)
    source_type: str = Field(min_length=1, max_length=50)
    external_id: str | None = Field(default=None, max_length=2000)

    title: str = Field(min_length=1)
    url: str = Field(min_length=1)

    author: str | None = Field(default=None, max_length=300)
    description: str | None = None
    raw_content: str | None = None
    language: str | None = Field(default=None, max_length=20)

    published_at: datetime | None = None
    
    publisher_country_code: str | None = Field(default=None, max_length=2)
    publisher_country_name: str | None = Field(default=None, max_length=100)
    publisher_country_method: str | None = Field(default=None, max_length=50)


class ArticleResponse(ArticleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    collected_at: datetime
    publisher_name: str
    publisher_url: str | None = None
    
    publisher_country_code: str | None = None
    publisher_country_name: str | None = None

    canonical_url: str | None = None
    extracted_content: str | None = None
    cleaned_content: str | None = None
    content_hash: str | None = Field(
        default=None,
        max_length=64,
    )
    extraction_status: str
    extraction_error: str | None = None
    processed_at: datetime | None = None

    # Intelligence enrichments — populated when a company context is available
    sentiment: str | None = None

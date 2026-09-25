from datetime import datetime

from pydantic import BaseModel, Field


class CollectedArticle(BaseModel):
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

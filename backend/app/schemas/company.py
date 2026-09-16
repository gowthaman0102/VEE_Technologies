from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    client_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    industry: str | None = Field(default=None, max_length=200)


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    name: str
    website: str | None
    industry: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ActiveCompanyResponse(BaseModel):
    id: int
    name: str

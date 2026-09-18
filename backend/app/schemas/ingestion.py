from pydantic import BaseModel, Field


class IngestionRunRequest(BaseModel):
    source_keys: list[str] | None = None
    per_source_limit: int | None = Field(
        default=None,
        ge=1,
        le=100,
    )
    max_age_days: int | None = Field(
        default=None,
        ge=1,
        le=36500,
    )


class SourceResponse(BaseModel):
    key: str
    name: str
    source_type: str
    language: str
    enabled: bool
    category: str | None = None


class SourceIngestionResponse(BaseModel):
    source_key: str
    source_name: str
    collected: int
    inserted: int
    skipped: int
    error: str | None = None


class IngestionRunResponse(BaseModel):
    sources: list[SourceIngestionResponse]
    total_collected: int
    total_inserted: int
    total_skipped: int
    failures: int

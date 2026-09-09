from pydantic import BaseModel, Field


class EmbeddingResultResponse(BaseModel):
    article_id: int
    status: str
    model: str | None = None
    dimensions: int | None = None
    error: str | None = None


class BatchEmbeddingRequest(BaseModel):
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    include_failed: bool = False


class BatchEmbeddingResponse(BaseModel):
    selected: int
    success: int
    skipped: int
    failed: int
    results: list[
        EmbeddingResultResponse
    ]


class EmbeddingStatusResponse(BaseModel):
    pending: int
    success: int
    skipped: int
    failed: int
    total: int

from pydantic import BaseModel, Field


class ProcessingResultResponse(BaseModel):
    article_id: int
    status: str
    duplicate_of_id: int | None = None
    content_hash: str | None = None
    error: str | None = None


class BatchProcessingRequest(BaseModel):
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    include_failed: bool = False


class BatchProcessingResponse(BaseModel):
    selected: int
    success: int
    skipped: int
    failed: int
    results: list[
        ProcessingResultResponse
    ]


class ProcessingStatusResponse(BaseModel):
    pending: int
    success: int
    skipped: int
    failed: int
    total: int

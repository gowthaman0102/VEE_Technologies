from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.article import Article
from app.schemas.processing import (
    BatchProcessingRequest,
    BatchProcessingResponse,
    ProcessingResultResponse,
    ProcessingStatusResponse,
)
from app.services.article_batch_processing_service import (
    process_articles_batch,
)
from app.services.article_processing_service import (
    process_article_by_id,
)


router = APIRouter(
    prefix="/processing",
    tags=["Processing"],
)


@router.post(
    "/articles/{article_id}",
    response_model=ProcessingResultResponse,
)
async def process_single_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProcessingResultResponse:
    result = await process_article_by_id(
        db,
        article_id=article_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    return ProcessingResultResponse(
        article_id=result.article_id,
        status=result.status,
        duplicate_of_id=(
            result.duplicate_of_id
        ),
        content_hash=result.content_hash,
        error=result.error,
    )


@router.post(
    "/batch",
    response_model=BatchProcessingResponse,
)
async def process_batch(
    request: BatchProcessingRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchProcessingResponse:
    result = await process_articles_batch(
        db,
        limit=request.limit,
        include_failed=(
            request.include_failed
        ),
    )

    return BatchProcessingResponse(
        selected=result.selected,
        success=result.success,
        skipped=result.skipped,
        failed=result.failed,
        results=[
            ProcessingResultResponse(
                article_id=item.article_id,
                status=item.status,
                duplicate_of_id=(
                    item.duplicate_of_id
                ),
                content_hash=(
                    item.content_hash
                ),
                error=item.error,
            )
            for item in result.results
        ],
    )


@router.get(
    "/status",
    response_model=ProcessingStatusResponse,
)
async def get_processing_status(
    db: AsyncSession = Depends(get_db),
) -> ProcessingStatusResponse:
    result = await db.execute(
        select(
            Article.extraction_status,
            func.count(Article.id),
        )
        .group_by(
            Article.extraction_status
        )
    )

    counts = {
        status: count
        for status, count in result.all()
    }

    total = sum(counts.values())

    return ProcessingStatusResponse(
        pending=counts.get(
            "pending",
            0,
        ),
        success=counts.get(
            "success",
            0,
        ),
        skipped=counts.get(
            "skipped",
            0,
        ),
        failed=counts.get(
            "failed",
            0,
        ),
        total=total,
    )

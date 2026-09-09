from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.article import Article
from app.schemas.embeddings import (
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    EmbeddingResultResponse,
    EmbeddingStatusResponse,
)
from app.services.article_embedding_batch_service import (
    process_embedding_batch,
)
from app.services.article_embedding_service import (
    embed_article_by_id,
)


router = APIRouter(
    prefix="/embeddings",
    tags=["Embeddings"],
)


@router.post(
    "/articles/{article_id}",
    response_model=EmbeddingResultResponse,
)
async def embed_single_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> EmbeddingResultResponse:
    result = await embed_article_by_id(
        db,
        article_id=article_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    return EmbeddingResultResponse(
        article_id=result.article_id,
        status=result.status,
        model=result.model,
        dimensions=result.dimensions,
        error=result.error,
    )


@router.post(
    "/batch",
    response_model=BatchEmbeddingResponse,
)
async def embed_batch(
    request: BatchEmbeddingRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchEmbeddingResponse:
    result = await process_embedding_batch(
        db,
        limit=request.limit,
        include_failed=request.include_failed,
    )

    return BatchEmbeddingResponse(
        selected=result.selected,
        success=result.success,
        skipped=result.skipped,
        failed=result.failed,
        results=[
            EmbeddingResultResponse(
                article_id=item.article_id,
                status=item.status,
                model=item.model,
                dimensions=item.dimensions,
                error=item.error,
            )
            for item in result.results
        ],
    )


@router.get(
    "/status",
    response_model=EmbeddingStatusResponse,
)
async def get_embedding_status(
    db: AsyncSession = Depends(get_db),
) -> EmbeddingStatusResponse:
    result = await db.execute(
        select(
            Article.embedding_status,
            func.count(Article.id),
        )
        .group_by(
            Article.embedding_status
        )
    )

    counts = {
        status: count
        for status, count in result.all()
    }

    total = sum(counts.values())

    return EmbeddingStatusResponse(
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

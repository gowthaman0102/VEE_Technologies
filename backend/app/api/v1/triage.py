from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.article_triage_api import (
    ArticleTriageBatchItemResponse,
    ArticleTriageBatchRequest,
    ArticleTriageBatchResponse,
    ArticleTriageRequest,
    ArticleTriageResponse,
    StoredArticleTriageResponse,
)
from app.services.article_triage_batch_service import (
    triage_articles_batch,
)
from app.services.article_triage_read_service import (
    get_article_triage,
)
from app.services.article_triage_service import (
    ArticleNotFoundError,
    CompanyNotFoundError,
    triage_article,
)


router = APIRouter(
    prefix="/triage",
    tags=["triage"],
)


@router.post(
    "/articles/{article_id}",
    response_model=ArticleTriageResponse,
)
async def run_article_triage(
    article_id: int,
    payload: ArticleTriageRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await triage_article(
            db,
            article_id=article_id,
            company_id=payload.company_id,
        )
    except (
        ArticleNotFoundError,
        CompanyNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ArticleTriageResponse(
        article_id=result.article_id,
        model=result.model,
        triage=result.triage,
    )


@router.get(
    "/articles/{article_id}",
    response_model=StoredArticleTriageResponse,
)
async def read_article_triage(
    article_id: int,
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    record = await get_article_triage(
        db,
        article_id=article_id,
        company_id=company_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored triage result not found.",
        )

    return StoredArticleTriageResponse(
        id=record.id,
        article_id=record.article_id,
        company_id=record.company_id,
        company_name=record.company_name,
        event_type=record.event_type,
        summary=record.summary,
        why_it_matters=record.why_it_matters,
        evidence=record.evidence,
        potential_impact=record.potential_impact,
        urgency=record.urgency,
        confidence=record.confidence,
        llm_model=record.llm_model,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/batch",
    response_model=ArticleTriageBatchResponse,
)
async def run_batch_triage(
    payload: ArticleTriageBatchRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await triage_articles_batch(
            db,
            article_ids=payload.article_ids,
            company_id=payload.company_id,
            rag_limit=payload.rag_limit,
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    items = []

    for item in result.items:
        if item.result is None:
            items.append(
                ArticleTriageBatchItemResponse(
                    article_id=item.article_id,
                    status=item.status,
                    error=item.error,
                )
            )
            continue

        items.append(
            ArticleTriageBatchItemResponse(
                article_id=item.article_id,
                status=item.status,
                model=item.result.model,
                triage=item.result.triage,
                error=item.error,
            )
        )

    return ArticleTriageBatchResponse(
        company_id=result.company_id,
        requested_count=result.requested_count,
        success_count=result.success_count,
        not_found_count=result.not_found_count,
        failed_count=result.failed_count,
        items=items,
    )

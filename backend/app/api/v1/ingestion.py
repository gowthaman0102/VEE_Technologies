from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.ingestion.multi_runner import run_sources
from app.ingestion.sources import (
    get_enabled_sources,
    get_source,
)
from app.schemas.ingestion import (
    IngestionRunRequest,
    IngestionRunResponse,
    SourceIngestionResponse,
    SourceResponse,
)


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


@router.get(
    "/sources",
    response_model=list[SourceResponse],
)
async def list_ingestion_sources() -> list[SourceResponse]:
    sources = get_enabled_sources()

    return [
        SourceResponse(
            key=source.key,
            name=source.name,
            source_type=source.source_type,
            language=source.language,
            enabled=source.enabled,
            category=source.category,
        )
        for source in sources
    ]


@router.post(
    "/run",
    response_model=IngestionRunResponse,
)
async def run_ingestion(
    request: IngestionRunRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionRunResponse:
    if request.source_keys:
        sources = []

        for key in request.source_keys:
            source = get_source(key)

            if source is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Unknown source: {key}"
                    ),
                )

            if not source.enabled:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Source is disabled: {key}"
                    ),
                )

            sources.append(source)

    else:
        sources = get_enabled_sources()

    results = await run_sources(
        db=db,
        sources=sources,
        newsapi_api_key=(
            settings.newsapi_api_key
        ),
        newsapi_base_url=(
            settings.newsapi_base_url
        ),
        per_source_limit=(
            request.per_source_limit
        ),
        max_age_days=(
            request.max_age_days
            if request.max_age_days is not None
            else 30
        ),
    )

    response_results = [
        SourceIngestionResponse(
            source_key=result.source_key,
            source_name=result.source_name,
            collected=result.collected,
            inserted=result.inserted,
            skipped=result.skipped,
            error=result.error,
        )
        for result in results
    ]

    return IngestionRunResponse(
        sources=response_results,
        total_collected=sum(
            result.collected
            for result in results
        ),
        total_inserted=sum(
            result.inserted
            for result in results
        ),
        total_skipped=sum(
            result.skipped
            for result in results
        ),
        failures=sum(
            1
            for result in results
            if result.error is not None
        ),
    )


@router.post(
    "/run/{source_key}",
    response_model=IngestionRunResponse,
)
async def run_single_source(
    source_key: str,
    request: IngestionRunRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionRunResponse:
    source = get_source(source_key)

    if source is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown source: {source_key}"
            ),
        )

    if not source.enabled:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Source is disabled: {source_key}"
            ),
        )

    results = await run_sources(
        db=db,
        sources=[source],
        newsapi_api_key=(
            settings.newsapi_api_key
        ),
        newsapi_base_url=(
            settings.newsapi_base_url
        ),
        per_source_limit=(
            request.per_source_limit
        ),
        max_age_days=(
            request.max_age_days
            if request.max_age_days is not None
            else 30
        ),
    )

    response_results = [
        SourceIngestionResponse(
            source_key=result.source_key,
            source_name=result.source_name,
            collected=result.collected,
            inserted=result.inserted,
            skipped=result.skipped,
            error=result.error,
        )
        for result in results
    ]

    return IngestionRunResponse(
        sources=response_results,
        total_collected=sum(
            result.collected
            for result in results
        ),
        total_inserted=sum(
            result.inserted
            for result in results
        ),
        total_skipped=sum(
            result.skipped
            for result in results
        ),
        failures=sum(
            1
            for result in results
            if result.error is not None
        ),
    )

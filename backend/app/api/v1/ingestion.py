from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.celery_app import celery_app
from app.db.session import get_db
from app.ingestion.multi_runner import run_sources
from app.ingestion.sources import (
    get_sources_for_config,
)
from app.schemas.ingestion import (
    IngestionRunRequest,
    IngestionRunResponse,
    SourceIngestionResponse,
    SourceResponse,
)
from app.services.active_company_profile_service import get_active_company_profile
from app.services.client_configuration_service import get_client_config


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


def _queue_processing_tasks(
    results: list,
    company_id: int,
) -> None:
    for result in results:
        for article_id in result.inserted_article_ids:
            try:
                celery_app.send_task(
                    "processing.process_article",
                    args=[article_id, company_id],
                )
            except Exception:
                continue


@router.get(
    "/sources",
    response_model=list[SourceResponse],
)
async def list_ingestion_sources(
    db: AsyncSession = Depends(get_db),
) -> list[SourceResponse]:
    profile = await get_active_company_profile(db)
    if profile is None:
        raise HTTPException(status_code=404, detail="No active company configured")
    config = await get_client_config(db, profile.company_id)
    sources = get_sources_for_config(config)

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
    profile = await get_active_company_profile(db)
    if profile is None:
        raise HTTPException(status_code=404, detail="No active company configured")
    config = await get_client_config(db, profile.company_id)
    available_sources = get_sources_for_config(config)
    sources_by_key = {source.key: source for source in available_sources}

    if request.source_keys:
        sources = []

        for key in request.source_keys:
            source = sources_by_key.get(key)

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
        sources = available_sources

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
    _queue_processing_tasks(results, profile.company_id)

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
    profile = await get_active_company_profile(db)
    if profile is None:
        raise HTTPException(status_code=404, detail="No active company configured")
    config = await get_client_config(db, profile.company_id)
    source = next(
        (item for item in get_sources_for_config(config) if item.key == source_key),
        None,
    )

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
    _queue_processing_tasks(results, profile.company_id)

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

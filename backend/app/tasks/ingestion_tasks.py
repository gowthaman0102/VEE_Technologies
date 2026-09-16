import asyncio

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.ingestion.multi_runner import run_sources
from app.ingestion.sources import (
    get_enabled_sources,
)
from app.services.active_company_profile_service import (
    get_active_company_profile,
)


async def _run_live_ingestion() -> dict:
    sources = get_enabled_sources()

    async with CeleryAsyncSessionLocal() as db:
        profile = await get_active_company_profile(
            db
        )

        if profile is None:
            raise RuntimeError(
                "No active company configured"
            )

        results = await run_sources(
            db=db,
            sources=sources,
            newsapi_api_key=(
                settings.newsapi_api_key
            ),
            newsapi_base_url=(
                settings.newsapi_base_url
            ),
            per_source_limit=20,
        )

    inserted_article_ids = [
        article_id
        for result in results
        for article_id in (
            result.inserted_article_ids
        )
    ]

    for article_id in inserted_article_ids:
        celery_app.send_task(
            "processing.process_article",
            args=[
                article_id,
                profile.company_id,
            ],
        )

    source_results = [
        {
            "source_key": result.source_key,
            "source_name": result.source_name,
            "collected": result.collected,
            "inserted": result.inserted,
            "skipped": result.skipped,
            "inserted_article_ids": (
                result.inserted_article_ids
            ),
            "error": result.error,
        }
        for result in results
    ]

    return {
        "sources": source_results,
        "total_collected": sum(
            item["collected"]
            for item in source_results
        ),
        "total_inserted": sum(
            item["inserted"]
            for item in source_results
        ),
        "total_skipped": sum(
            item["skipped"]
            for item in source_results
        ),
        "inserted_article_ids": (
            inserted_article_ids
        ),
        "processing_tasks_queued": len(
            inserted_article_ids
        ),
        "failures": sum(
            1
            for item in source_results
            if item["error"] is not None
        ),
    }


@celery_app.task(
    bind=True,
    name="ingestion.live_poll",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def live_ingestion_task(
    self,
) -> dict:
    return asyncio.run(
        _run_live_ingestion()
    )

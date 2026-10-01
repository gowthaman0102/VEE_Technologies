import asyncio

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.ingestion.multi_runner import run_sources
from app.ingestion.sources import get_enabled_sources, get_sources_for_config
from app.services.active_company_profile_service import (
    get_active_company_profile,
)
from app.services.client_configuration_service import get_client_config


async def _get_ingestion_sources(db, company_id: int):
    try:
        config = await get_client_config(db, company_id)
    except AttributeError:
        # Keep lightweight task tests and older task callers compatible.
        return get_enabled_sources()
    return get_sources_for_config(config)


import redis.asyncio as redis
from sqlalchemy import insert
from datetime import datetime, timezone
from app.models.ingestion_run import IngestionRun

async def _run_live_ingestion() -> dict:
    async with CeleryAsyncSessionLocal() as db:
        profile = await get_active_company_profile(db)
        if profile is None:
            raise RuntimeError("No active company configured")
            
        company_id = profile.company_id
        lock_key = f"nova:ingestion:lock:{company_id}"
        
        # Redis Lock
        redis_client = redis.from_url(settings.redis_url)
        try:
            # Attempt to acquire lock for 4 minutes
            acquired = await redis_client.set(lock_key, "1", nx=True, ex=240)
            if not acquired:
                return {"status": "skipped", "reason": "lock_active"}

            sources = await _get_ingestion_sources(db, company_id)
            
            # Start run record
            run = IngestionRun(
                company_id=company_id,
                started_at=datetime.now(timezone.utc),
                status="processing"
            )
            db.add(run)
            await db.commit()
            await db.refresh(run)

            from app.services.live_feed_service import publish_live_event
            await publish_live_event("ingestion_started", company_id)

            try:
                results = await run_sources(
                    db=db,
                    sources=sources,
                    newsapi_api_key=settings.newsapi_api_key,
                    newsapi_base_url=settings.newsapi_base_url,
                    per_source_limit=20,
                    max_age_days=30,
                )
                
                inserted_article_ids = [
                    article_id for result in results for article_id in result.inserted_article_ids
                ]

                for article_id in inserted_article_ids:
                    celery_app.send_task(
                        "processing.process_article",
                        args=[article_id, company_id],
                    )

                source_results = [
                    {
                        "source_key": result.source_key,
                        "source_name": result.source_name,
                        "collected": result.collected,
                        "inserted": result.inserted,
                        "skipped": result.skipped,
                        "error": result.error,
                    }
                    for result in results
                ]
                
                run.completed_at = datetime.now(timezone.utc)
                run.status = "completed"
                run.total_collected = sum(item["collected"] for item in source_results)
                run.total_inserted = sum(item["inserted"] for item in source_results)
                run.total_skipped = sum(item["skipped"] for item in source_results)
                run.failure_count = sum(1 for item in source_results if item["error"] is not None)
                run.source_metadata = {"sources": source_results}
                
                await db.commit()

                if inserted_article_ids:
                    await publish_live_event("article_inserted", company_id, {"count": len(inserted_article_ids)})
                await publish_live_event("ingestion_completed", company_id, {"inserted": run.total_inserted})

                return {
                    "sources": source_results,
                    "total_collected": run.total_collected,
                    "total_inserted": run.total_inserted,
                    "total_skipped": run.total_skipped,
                    "inserted_article_ids": inserted_article_ids,
                    "processing_tasks_queued": len(inserted_article_ids),
                    "failures": run.failure_count,
                }
            except Exception as e:
                run.completed_at = datetime.now(timezone.utc)
                run.status = "failed"
                await db.commit()
                raise e
        finally:
            # Only delete lock if we acquired it
            if acquired:
                await redis_client.delete(lock_key)
            await redis_client.close()


async def _run_historical_backfill(
    *,
    max_age_days: int = 3650,
    per_source_limit: int | None = 100,
) -> dict:
    async with CeleryAsyncSessionLocal() as db:
        profile = await get_active_company_profile(
            db
        )

        if profile is None:
            raise RuntimeError(
                "No active company configured"
            )

        sources = await _get_ingestion_sources(db, profile.company_id)

        results = await run_sources(
            db=db,
            sources=sources,
            newsapi_api_key=(
                settings.newsapi_api_key
            ),
            newsapi_base_url=(
                settings.newsapi_base_url
            ),
            per_source_limit=per_source_limit,
            max_age_days=max_age_days,
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

    return {
        "sources": [
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
        ],
        "total_collected": sum(
            result.collected for result in results
        ),
        "total_inserted": sum(
            result.inserted for result in results
        ),
        "total_skipped": sum(
            result.skipped for result in results
        ),
        "inserted_article_ids": (
            inserted_article_ids
        ),
        "processing_tasks_queued": len(
            inserted_article_ids
        ),
        "failures": sum(
            1
            for result in results
            if result.error is not None
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


@celery_app.task(
    bind=True,
    name="ingestion.historical_backfill",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def historical_backfill_task(
    self,
    max_age_days: int = 3650,
    per_source_limit: int | None = 100,
) -> dict:
    return asyncio.run(
        _run_historical_backfill(
            max_age_days=max_age_days,
            per_source_limit=per_source_limit,
        )
    )

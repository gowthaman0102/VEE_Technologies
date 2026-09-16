import asyncio

from app.core.celery_app import celery_app
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.services.article_processing_service import (
    process_article_by_id,
)


async def _process_article_pipeline(
    *,
    article_id: int,
    company_id: int,
) -> dict:
    async with CeleryAsyncSessionLocal() as db:
        result = await process_article_by_id(
            db,
            article_id=article_id,
        )

    if result is None:
        return {
            "article_id": article_id,
            "company_id": company_id,
            "status": "not_found",
            "intelligence_queued": False,
        }

    intelligence_queued = False

    if result.status == "success":
        celery_app.send_task(
            "intelligence.process_article",
            args=[
                article_id,
                company_id,
            ],
        )

        intelligence_queued = True

    return {
        "article_id": result.article_id,
        "company_id": company_id,
        "status": result.status,
        "duplicate_of_id": (
            result.duplicate_of_id
        ),
        "content_hash": (
            result.content_hash
        ),
        "error": result.error,
        "intelligence_queued": (
            intelligence_queued
        ),
    }


@celery_app.task(
    bind=True,
    name="processing.process_article",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def process_article_pipeline_task(
    self,
    article_id: int,
    company_id: int,
) -> dict:
    return asyncio.run(
        _process_article_pipeline(
            article_id=article_id,
            company_id=company_id,
        )
    )

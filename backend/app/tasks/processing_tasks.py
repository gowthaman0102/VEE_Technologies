import asyncio

from app.core.celery_app import celery_app
from app.db.celery_session import (
    CeleryAsyncSessionLocal,
)
from app.services.article_embedding_service import (
    embed_article_by_id,
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
                "embedding_status": "not_run",
                "intelligence_queued": False,
            }

        embedding_result = None

        if result.status == "success":
            embedding_result = await embed_article_by_id(
                db,
                article_id=article_id,
            )

    intelligence_queued = False

    if (
        result.status == "success"
        and embedding_result is not None
        and embedding_result.status == "success"
    ):
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
        "embedding_status": (
            embedding_result.status
            if embedding_result is not None
            else "not_run"
        ),
        "embedding_model": (
            embedding_result.model
            if embedding_result is not None
            else None
        ),
        "embedding_error": (
            embedding_result.error
            if embedding_result is not None
            else None
        ),
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

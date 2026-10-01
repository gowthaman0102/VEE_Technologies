from datetime import datetime, timezone

from app.core.celery_app import celery_app


@celery_app.task(
    name="system.health_check",
)
def health_check_task() -> dict:
    return {
        "status": "ok",
        "worker": "celery",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }


import asyncio
from app.db.celery_session import CeleryAsyncSessionLocal
from app.models.ingestion_run import IngestionRun
from sqlalchemy import select
from app.services.article_recovery_service import queue_incomplete_active_articles
import logging

logger = logging.getLogger(__name__)

async def _run_stale_feed_watchdog():
    async with CeleryAsyncSessionLocal() as db:
        # Check staleness
        latest_run = await db.scalar(
            select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(1)
        )
        now = datetime.now(timezone.utc)
        
        # Stale threshold: e.g. 15 minutes
        is_stale = False
        if latest_run is None:
            is_stale = True
        elif latest_run.completed_at is None:
            if (now - latest_run.started_at).total_seconds() > 900:
                is_stale = True
        else:
            if (now - latest_run.completed_at).total_seconds() > 900:
                is_stale = True
                
        if is_stale:
            logger.warning("Feed appears stale. Initiating recovery queue.")
            # Trigger recovery
            await queue_incomplete_active_articles(db)

@celery_app.task(
    name="system.stale_feed_watchdog",
)
def stale_feed_watchdog_task() -> dict:
    asyncio.run(_run_stale_feed_watchdog())
    return {"status": "ok"}


import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.ingestion_run import IngestionRun
from app.models.article import Article
from app.models.article_triage import ArticleTriage
from app.models.article_sentiment import ArticleSentiment
from app.models.risk_assessment import RiskAssessment
from app.services.active_company_profile_service import get_active_company_profile

router = APIRouter(prefix="/live", tags=["Live"])

def _format_sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"

@router.get("/status")
async def get_live_status(db: AsyncSession = Depends(get_db)):
    profile = await get_active_company_profile(db)
    if not profile:
        return {"status": "offline"}

    company_id = profile.company_id
    
    last_run = await db.scalar(
        select(IngestionRun)
        .where(IngestionRun.company_id == company_id)
        .order_by(IngestionRun.started_at.desc())
        .limit(1)
    )
    
    last_successful = await db.scalar(
        select(IngestionRun)
        .where(IngestionRun.company_id == company_id, IngestionRun.status == "completed")
        .order_by(IngestionRun.started_at.desc())
        .limit(1)
    )
    
    last_article = await db.scalar(
        select(Article.created_at)
        .where(Article.company_id == company_id)
        .order_by(Article.id.desc())
        .limit(1)
    )
    
    last_processed = await db.scalar(
        select(ArticleTriage.created_at)
        .where(ArticleTriage.company_id == company_id)
        .order_by(ArticleTriage.id.desc())
        .limit(1)
    )

    now = datetime.now(timezone.utc)
    status = "offline"
    
    if last_run:
        if last_run.completed_at and (now - last_run.completed_at).total_seconds() < 900:
            status = "live"
        elif not last_run.completed_at and (now - last_run.started_at).total_seconds() < 900:
            status = "processing"
        else:
            status = "delayed"

    # Compute a quick data version based on max timestamps
    max_ts = max(
        filter(None, [
            last_article,
            last_processed,
            last_run.completed_at if last_run else None
        ]),
        default=datetime.min.replace(tzinfo=timezone.utc)
    )
    
    return {
        "server_time": now.isoformat(),
        "status": status,
        "last_poll_started_at": last_run.started_at.isoformat() if last_run else None,
        "last_poll_completed_at": last_run.completed_at.isoformat() if last_run and last_run.completed_at else None,
        "last_successful_poll_at": last_successful.completed_at.isoformat() if last_successful and last_successful.completed_at else None,
        "last_article_inserted_at": last_article.isoformat() if last_article else None,
        "last_article_processed_at": last_processed.isoformat() if last_processed else None,
        "last_run": {
            "collected": last_run.total_collected if last_run else 0,
            "inserted": last_run.total_inserted if last_run else 0,
            "skipped": last_run.total_skipped if last_run else 0,
            "failures": last_run.failure_count if last_run else 0,
        },
        "processing": {
            "processed_total": 0,  # We can calculate this, but status is lightweight
            "pending": 0,
        },
        "data_version": int(max_ts.timestamp())
    }

@router.get("/stream")
async def live_stream():
    import json
    
    async def event_generator() -> AsyncGenerator[str, None]:
        # Connect to redis pubsub
        import redis.asyncio as redis
        from app.core.config import settings
        
        redis_client = redis.from_url(settings.redis_url)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("nova:live_events")
        
        try:
            while True:
                # Poll pubsub
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    try:
                        data = json.loads(message["data"])
                        event = data.get("type", "update")
                        payload = data.get("payload", {})
                        yield _format_sse(event, json.dumps(payload))
                    except:
                        pass
                
                # Yield heartbeat every 2 seconds if no other messages
                yield _format_sse("heartbeat", json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()}))
        finally:
            await pubsub.unsubscribe("nova:live_events")
            await redis_client.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

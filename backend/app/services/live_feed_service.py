import json
import redis.asyncio as redis
from app.core.config import settings

async def publish_live_event(event_type: str, company_id: int, payload: dict = None):
    try:
        if payload is None:
            payload = {}
        payload["company_id"] = company_id
        
        client = redis.from_url(settings.redis_url)
        message = json.dumps({"type": event_type, "payload": payload})
        await client.publish("nova:live_events", message)
        await client.close()
    except Exception:
        pass

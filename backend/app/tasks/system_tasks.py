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

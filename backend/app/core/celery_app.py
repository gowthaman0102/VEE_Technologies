from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "media_intelligence",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.imports = (
    "app.tasks.system_tasks",
    "app.tasks.intelligence_tasks",
    "app.tasks.alert_tasks",
    "app.tasks.sla_tasks",
    "app.tasks.ingestion_tasks",
    "app.tasks.processing_tasks",
    "app.tasks.report_tasks",
)

celery_app.conf.update(
    task_default_queue=settings.celery_task_default_queue,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_time_limit=(
        settings.celery_task_time_limit_seconds
    ),
    task_soft_time_limit=(
        settings.celery_task_soft_time_limit_seconds
    ),
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "live-news-poll-every-5-minutes": {
        "task": "ingestion.live_poll",
        "schedule": 300.0,
    },
    "generate-daily-intelligence-reports": {
        "task": "reports.generate_daily",
        "schedule": 86400.0,
    },
    "generate-weekly-intelligence-reports": {
        "task": "reports.generate_weekly",
        "schedule": 604800.0,
    },
    "generate-monthly-intelligence-reports": {
        "task": "reports.generate_monthly",
        "schedule": 2592000.0,
    },
}

from celery import Celery
from celery.schedules import crontab

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
    broker_transport_options={"protocol": 2},
    result_backend_transport_options={"protocol": 2},
    task_time_limit=settings.celery_task_time_limit_seconds,
    task_soft_time_limit=(
        settings.celery_task_soft_time_limit_seconds
    ),
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "live-news-poll-interval": {
        "task": "ingestion.live_poll",
        "schedule": float(settings.live_ingestion_interval_seconds),
    },
    "stale-feed-watchdog-every-5-minutes": {
        "task": "system.stale_feed_watchdog",
        "schedule": 300.0,
    },
    "run-user-report-schedules-every-5-minutes": {
        "task": "reports.run_due_schedules",
        "schedule": 300.0,
    },
    "generate-daily-intelligence-reports": {
        "task": "reports.generate_daily",
        "schedule": crontab(
            minute=10,
            hour=0,
        ),
    },
    "generate-weekly-intelligence-reports": {
        "task": "reports.generate_weekly",
        "schedule": crontab(
            minute=20,
            hour=0,
            day_of_week="monday",
        ),
    },
    "generate-monthly-intelligence-reports": {
        "task": "reports.generate_monthly",
        "schedule": crontab(
            minute=30,
            hour=0,
            day_of_month="1",
        ),
    },
}

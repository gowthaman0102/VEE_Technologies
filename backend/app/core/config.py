from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "AI Media Intelligence"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://media_user:change_me@localhost:5432/media_intelligence"
    )

    newsapi_api_key: str | None = None
    newsapi_base_url: str = "https://newsapi.org/v2"

    openai_api_key: str | None = None

    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    semantic_relevance_threshold: float = 0.45

    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    llm_timeout_seconds: float = 120.0

    redis_url: str = "redis://127.0.0.1:6379/0"
    celery_broker_url: str = "redis://127.0.0.1:6379/0"
    celery_result_backend: str = "redis://127.0.0.1:6379/1"
    celery_task_default_queue: str = "media-intelligence"
    celery_task_time_limit_seconds: int = 300
    celery_task_soft_time_limit_seconds: int = 270

    alert_delivery_provider: str = "slack"
    alert_delivery_timeout_seconds: float = 10.0
    alert_delivery_max_retries: int = 3
    slack_webhook_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

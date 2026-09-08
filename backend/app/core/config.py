from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Media Intelligence"
    app_env: str = "development"
    debug: bool = True

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    database_url: str = ""
    redis_url: str = ""

    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    embedding_provider: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""

    news_api_key: str = ""
    slack_webhook_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

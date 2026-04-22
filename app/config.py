from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "AI Agent Gateway"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./gateway.db"

    rate_limit_window: int = 60
    rate_limit_max_requests: int = 100

    admin_api_key: str = "admin-secret-key"

    log_request_body: bool = True
    log_response_body: bool = True

    default_timeout: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()

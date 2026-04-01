from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = Field(default="local")
    api_title: str = Field(default="Finfluencer Analysis API")
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@db:5432/finfluencer")
    database_url_sync: str | None = None

    # Optional sqlite persistence (without Cloud SQL): backup SQLite db to GCS regularly.
    enable_sqlite_persistence: bool = True
    sqlite_backup_bucket: str | None = None
    sqlite_backup_prefix: str = "finfluencer-mvp"
    sqlite_persistence_interval_seconds: int = 300

    youtube_api_key: str | None = None
    yt_api_base: str = "https://www.googleapis.com/youtube/v3"

    admin_token: str = Field(default="dev-admin-token")
    timezone: str = "UTC"
    poller_interval_seconds: int = 300

    llm_provider: Literal["openai", "gemini", "mock"] = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    prompt_version: str = "v1.0"
    taxonomy_version: str = "v1.0"

    stt_enabled: bool = True
    stt_chunk_seconds: int = 900
    stt_max_video_minutes: int = 90

    retry_max_attempts: int = 5
    retry_backoff_base_seconds: float = 1.5

    worker_poll_interval_seconds: float = 3.0
    worker_batch_size: int = 8

    stt_use_mock_when_missing: bool = True
    transcript_provider_preferred: str = "public_transcript"

    @property
    def database_url_sync_or_async(self) -> str:
        return self.database_url_sync or self.database_url


settings = Settings()

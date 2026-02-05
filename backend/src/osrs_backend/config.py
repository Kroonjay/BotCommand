"""Shared configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    postgres_prisma_url: str = "postgresql://localhost:5432/osrs"

    # Redis
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379

    # HTTP Server
    http_host: str = "0.0.0.0"
    http_port: int = 8080

    # TCP Server (ML inference)
    tcp_host: str = "127.0.0.1"
    tcp_port: int = 9999

    # ML Settings
    ml_device: str = "cpu"
    ml_processor_pool_size: int = 1
    ml_processor_type: str = "thread"

    # Models directory (relative to repo root)
    models_dir: str = "../pvp-ml/models"

    # Wiki API (for price fetching)
    wiki_api_base_url: str = "https://prices.runescape.wiki/api/v1/osrs"
    wiki_api_user_agent: str = "osrs-backend/1.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for local development. In production, these are injected via the container
orchestration platform (Kubernetes secrets, AWS Secrets Manager, etc.).
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────
    APP_NAME: str = "Knowledge Factory"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Database ───────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://kf_user:kf_password@localhost:5432/knowledge_factory"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ── Redis ──────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT / Security ─────────────────────────────────────────────
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_SECRET_KEY: str = "dev-stable-secret-change-in-production"
    JWT_ACCESS_TTL_MINUTES: int = 60
    JWT_REFRESH_TTL_DAYS: int = 7

    # ── AI Question Generation ─────────────────────────────────────
    AI_API_URL: str = "http://Code7-ai-alb-120690216.ap-south-1.elb.amazonaws.com/v1/chat/completions"
    AI_API_KEY: str = "sk-8YoGZvol4JFZGXbWC0hFlg"
    AI_MODEL: str = "qwen3-coder-30b"

    # ── Code Execution Sandbox ─────────────────────────────────────
    SANDBOX_URL: str = "http://judge0:2358"
    SANDBOX_API_KEY: str = ""

    # ── Object Storage (S3-compatible) ─────────────────────────────
    S3_BUCKET_NAME: str = "knowledge-factory"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    # ── Redis ──────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT / Security ─────────────────────────────────────────────
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_SECRET_KEY: str = "dev-stable-secret-change-in-production"
    JWT_ACCESS_TTL_MINUTES: int = 60
    JWT_REFRESH_TTL_DAYS: int = 7

    # ── AI Question Generation ─────────────────────────────────────
    AI_API_URL: str = "http://localhost:8000/v1/chat/completions"
    AI_API_KEY: str = ""
    AI_MODEL: str = "qwen3-coder-30b"

    # ── Code Execution Sandbox ─────────────────────────────────────
    SANDBOX_URL: str = "http://localhost:8000"

    # ── Notifications ──────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""

    # ── Proctoring ─────────────────────────────────────────────────
    PROCTORING_MAX_WARNINGS: int = 3
    PROCTORING_EVENT_INTERVAL_SECONDS: int = 5

    # ── Rate Limiting ──────────────────────────────────────────────
    LOGIN_RATE_LIMIT: str = "5/15min"
    CODE_EXEC_RATE_LIMIT: str = "20/minute"

    # ── Seed Credentials (read from env, never hardcoded) ──────────
    SEED_ADMIN_PASSWORD: str = ""
    SEED_HR_PASSWORD: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level instance for direct imports (e.g., from app.config import settings)
settings = Settings()

__all__ = ["settings", "get_settings", "Settings"]

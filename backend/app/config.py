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
    # Local development: SQLite (single file, no server needed)
    # Production: Set to postgresql+asyncpg://... for PostgreSQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./knowledge_factory.db"
    DB_POOL_SIZE: int = 5  # SQLite uses connection pooling differently
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ── Redis ──────────────────────────────────────────────────────
    # Optional for local development (session cache, task queue)
    # Leave empty to disable Redis features
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
    SANDBOX_URL: str = "https://emkc.org/api/v2/piston/execute"
    SANDBOX_API_KEY: str = ""

    # ── Object Storage (S3-compatible) ─────────────────────────────
    S3_BUCKET_NAME: str = "knowledge-factory"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    # ── Notifications ──────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""

    # ── Proctoring ─────────────────────────────────────────────────
    PROCTORING_MAX_WARNINGS: int = 3
    PROCTORING_EVENT_INTERVAL_SECONDS: int = 5
    PROCTORING_SERVICE_WS_URL: str = "ws://localhost:8000"
    PROCTORING_JWT_SECRET: str = "dev-proctoring-secret-stable"
    
    # ── Proctoring Risk Weights ────────────────────────────────────
    TAB_SWITCH_WEIGHT: float = 10
    COPY_PASTE_WEIGHT: float = 10
    WINDOW_BLUR_WEIGHT: float = 15
    NO_FACE_WEIGHT: float = 20
    VOICE_DETECTED_WEIGHT: float = 15
    MULTIPLE_PERSON_WEIGHT: float = 60
    PHONE_DETECTED_WEIGHT: float = 80
    FULLSCREEN_EXIT_WEIGHT: float = 20
    
    # ── Proctoring Risk Management ─────────────────────────────────
    RISK_TERMINATION_THRESHOLD: float = 100
    RISK_DECAY_PERCENT: float = 0.05  # 5% decay
    RISK_DECAY_INTERVAL: int = 10     # Every 10 seconds
    FRAME_CAPTURE_INTERVAL: float = 1.0
    SCREENSHOT_STORAGE_PATH: str = "screenshots"
    HIGH_RISK_AUTO_TERMINATE: bool = True
    WEBSOCKET_HEARTBEAT_TIMEOUT: int = 30

    # ── Rate Limiting ──────────────────────────────────────────────
    LOGIN_RATE_LIMIT: str = "5/15min"
    CODE_EXEC_RATE_LIMIT: str = "20/minute"

    # ── Seed Credentials (read from env, never hardcoded) ──────────
    SEED_ADMIN_PASSWORD: str = ""
    SEED_HR_PASSWORD: str = ""

    # ── Feature Flags ──────────────────────────────────────────────
    ENABLE_EMAIL_VERIFICATION: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level instance for direct imports (e.g., from app.config import settings)
settings = Settings()

__all__ = ["settings", "get_settings", "Settings"]

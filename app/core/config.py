"""
Application configuration loaded from environment variables (.env).
Never hardcode secrets here.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "UniDocs Mobile API"
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./unidocs_dev.db"

    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    # File storage
    STORAGE_BACKEND: str = "local"  # local | s3 | supabase
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["*"]

    # Supabase (Optional, for permanent storage)
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRzZnZqaGh4a3ZzYm5jdmR4Y2tiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjczMzQ1NywiZXhwIjoyMTAyMzA5NDU3fQ.9WbBl697FiwIXhNdv_gz2EUuPkdodSOtkJ5Zwp7MIUM"
    SUPABASE_BUCKET: str = "unidocs"

    # Moderation
    REVIEW_LOCK_MINUTES: int = 15

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_UPLOAD: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Initial admin (used only by seed_admin CLI, never committed with real values)
    INITIAL_ADMIN_EMAIL: str = "admin@unidocs.local"
    INITIAL_ADMIN_PASSWORD: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

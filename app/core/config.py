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
<<<<<<< HEAD
    DATABASE_URL: str = "sqlite:///./storage/unidocs.db"
=======
    DATABASE_URL: str = "sqlite:///./unidocs_dev.db"
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)

    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    # File storage
    STORAGE_BACKEND: str = "local"  # local | s3
    STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 50
<<<<<<< HEAD
    ALLOWED_EXTENSIONS: List[str] = ["pdf"]
=======
    ALLOWED_EXTENSIONS: List[str] = ["*"]
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)

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
<<<<<<< HEAD
    INITIAL_ADMIN_EMAIL: str = "admin@unidocs.com"
    INITIAL_ADMIN_PASSWORD: str = "admin123456"
=======
    INITIAL_ADMIN_EMAIL: str = "admin@unidocs.local"
    INITIAL_ADMIN_PASSWORD: str = ""
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)


@lru_cache
def get_settings() -> Settings:
    return Settings()

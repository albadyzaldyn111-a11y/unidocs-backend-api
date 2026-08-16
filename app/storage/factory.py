from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageService
from app.storage.local import LocalStorage
from app.storage.supabase import SupabaseStorage


@lru_cache
def get_storage() -> StorageService:
    settings = get_settings()
    backend = settings.STORAGE_BACKEND.strip().lower()
    if backend == "s3":
        from app.storage.s3 import S3Storage

        return S3Storage(bucket="unidocs-files")
    if backend == "supabase":
        return SupabaseStorage(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_KEY,
            bucket=settings.SUPABASE_BUCKET,
        )
    if backend == "local":
        return LocalStorage(settings.STORAGE_PATH)
    raise RuntimeError(f"Unsupported STORAGE_BACKEND: {settings.STORAGE_BACKEND}")

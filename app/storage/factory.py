from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageService
from app.storage.local import LocalStorage


@lru_cache
def get_storage() -> StorageService:
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        from app.storage.s3 import S3Storage
        return S3Storage(bucket="unidocs-files")
    elif settings.STORAGE_BACKEND == "supabase" and settings.SUPABASE_URL and settings.SUPABASE_KEY:
        from app.storage.supabase_backend import SupabaseStorage
        return SupabaseStorage(settings.SUPABASE_URL, settings.SUPABASE_KEY, settings.SUPABASE_BUCKET)
    return LocalStorage(settings.STORAGE_PATH)

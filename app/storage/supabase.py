import io
from typing import BinaryIO
from supabase import create_client, Client
from app.storage.base import StorageService
from app.core.config import get_settings

class SupabaseStorage(StorageService):
    def __init__(self, url: str, key: str, bucket: str = "unidocs"):
        self.client: Client = create_client(url, key)
        self.bucket = bucket
        # Ensure bucket exists (this might fail if key doesn't have permissions, 
        # but we assume the user set it up or it exists)
        try:
            self.client.storage.get_bucket(bucket)
        except Exception:
            # We don't try to create it here to avoid permission issues, 
            # the user should create it in the Supabase dashboard
            pass

    def save(self, key: str, file_obj: BinaryIO) -> str:
        # Supabase storage upload
        # file_obj is a BinaryIO, we need bytes
        content = file_obj.read()
        self.client.storage.from_(self.bucket).upload(
            path=key,
            file=content,
            file_options={"upsert": "true"}
        )
        return key

    def open(self, key: str) -> BinaryIO:
        # Download from Supabase
        res = self.client.storage.from_(self.bucket).download(key)
        return io.BytesIO(res)

    def delete(self, key: str) -> None:
        self.client.storage.from_(self.bucket).remove([key])

    def exists(self, key: str) -> bool:
        # Simple check by trying to get public URL or list
        # List files in the directory
        dir_path = "/".join(key.split("/")[:-1])
        filename = key.split("/")[-1]
        res = self.client.storage.from_(self.bucket).list(dir_path)
        return any(item['name'] == filename for item in res)

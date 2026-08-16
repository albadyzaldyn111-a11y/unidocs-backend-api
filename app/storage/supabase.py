from __future__ import annotations

import io
from typing import BinaryIO
from urllib.parse import quote

import httpx

from app.storage.base import StorageService


class SupabaseStorage(StorageService):
    """Storage adapter for Supabase Storage's REST object API.

    The backend must use the service-role key server-side. The key is never
    returned to the mobile client.
    """

    def __init__(self, *, url: str, key: str, bucket: str, timeout: float = 90.0):
        self.base_url = url.rstrip("/")
        self.key = key
        self.bucket = bucket
        self.timeout = timeout
        if not self.base_url or not self.key or not self.bucket:
            raise RuntimeError("Supabase Storage is not configured")

    def _object_url(self, key: str) -> str:
        safe_key = quote(key.lstrip("/"), safe="/")
        safe_bucket = quote(self.bucket, safe="")
        return f"{self.base_url}/storage/v1/object/{safe_bucket}/{safe_key}"

    def _download_url(self, key: str) -> str:
        safe_key = quote(key.lstrip("/"), safe="/")
        safe_bucket = quote(self.bucket, safe="")
        return f"{self.base_url}/storage/v1/object/authenticated/{safe_bucket}/{safe_key}"

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def save(self, key: str, file_obj: BinaryIO) -> str:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self._object_url(key),
                    headers={**self._headers("application/octet-stream"), "x-upsert": "false"},
                    content=file_obj,
                )
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Supabase upload connection failed: {exc}") from exc

        if response.status_code not in (200, 201):
            detail = response.text[:500]
            if response.status_code == 409:
                raise RuntimeError("Supabase object already exists")
            raise RuntimeError(f"Supabase upload failed ({response.status_code}): {detail}")
        return key

    def open(self, key: str) -> BinaryIO:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self._download_url(key), headers=self._headers())
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Supabase download connection failed: {exc}") from exc

        if response.status_code != 200:
            raise FileNotFoundError(f"Supabase object not found ({response.status_code})")
        return io.BytesIO(response.content)

    def delete(self, key: str) -> None:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.delete(self._object_url(key), headers=self._headers())
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Supabase delete connection failed: {exc}") from exc

        if response.status_code not in (200, 204, 404):
            raise RuntimeError(f"Supabase delete failed ({response.status_code}): {response.text[:500]}")

    def exists(self, key: str) -> bool:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.head(self._object_url(key), headers=self._headers())
        except httpx.HTTPError:
            return False
        return response.status_code == 200

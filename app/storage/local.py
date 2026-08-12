import os
from pathlib import Path
from typing import BinaryIO

from app.storage.base import StorageService


class LocalStorage(StorageService):
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, key: str) -> Path:
        # Prevent path traversal: resolve and ensure it stays under root.
        candidate = (self.root / key).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise ValueError("Invalid storage key")
        return candidate

    def save(self, key: str, file_obj: BinaryIO) -> str:
        path = self._safe_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as out:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                out.write(chunk)
        return key

    def open(self, key: str) -> BinaryIO:
        path = self._safe_path(key)
        return open(path, "rb")

    def delete(self, key: str) -> None:
        path = self._safe_path(key)
        if path.exists():
            os.remove(path)

    def exists(self, key: str) -> bool:
        return self._safe_path(key).exists()

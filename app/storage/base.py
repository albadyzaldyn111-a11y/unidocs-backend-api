from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageService(ABC):
    """Abstraction so the business logic never depends on where bytes live.
    Implementations: LocalStorage today; S3Storage/MinIO later, same interface."""

    @abstractmethod
    def save(self, key: str, file_obj: BinaryIO) -> str:
        """Persist file_obj under key. Returns the storage key actually used."""

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Return a readable binary stream for the stored object."""

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

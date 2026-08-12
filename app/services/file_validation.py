"""
Validation pipeline for uploaded files, executed in this exact order:
Receive -> Validate Size -> Validate Magic Bytes -> Calculate SHA-256
-> Search Existing Hash -> (reject duplicate | store)
Never trust the client-provided extension or MIME type.
"""
import hashlib
from dataclasses import dataclass

from app.core.errors import AppError

PDF_MAGIC = b"%PDF-"


@dataclass
class ValidatedFile:
    sha256: str
    size_bytes: int


def validate_size(size_bytes: int, max_mb: int) -> None:
    max_bytes = max_mb * 1024 * 1024
    if size_bytes <= 0:
        raise AppError("Empty file", "EMPTY_FILE", 422)
    if size_bytes > max_bytes:
        raise AppError(f"File exceeds the {max_mb}MB limit", "FILE_TOO_LARGE", 422)


def validate_magic_bytes(header: bytes) -> None:
    if not header.startswith(PDF_MAGIC):
        raise AppError("File is not a valid PDF", "INVALID_FILE_TYPE", 422)


def validate_extension(filename: str, allowed: list[str]) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed:
        raise AppError(f"Extension .{ext} is not allowed", "INVALID_EXTENSION", 422)


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_page_count(page_count: int, min_pages: int) -> None:
    if page_count < min_pages:
        raise AppError(f"PDF must contain at least {min_pages} page(s)", "PAGE_COUNT_TOO_LOW", 422)

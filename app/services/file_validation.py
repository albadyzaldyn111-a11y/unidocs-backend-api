<<<<<<< HEAD
"""
Validation pipeline for uploaded files, executed in this exact order:
Receive -> Validate Size -> Validate Magic Bytes -> Calculate SHA-256
-> Search Existing Hash -> (reject duplicate | store)
Never trust the client-provided extension or MIME type.
"""
=======
"""Validation helpers for arbitrary user-uploaded files."""
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
import hashlib
from dataclasses import dataclass

from app.core.errors import AppError

<<<<<<< HEAD
PDF_MAGIC = b"%PDF-"

=======
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)

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
<<<<<<< HEAD
    if not header.startswith(PDF_MAGIC):
        raise AppError("File is not a valid PDF", "INVALID_FILE_TYPE", 422)


def validate_extension(filename: str, allowed: list[str]) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed:
        raise AppError(f"Extension .{ext} is not allowed", "INVALID_EXTENSION", 422)
=======
    """Kept for backward compatibility; arbitrary formats have no shared signature."""
    if not header:
        raise AppError("Empty file", "EMPTY_FILE", 422)


def validate_extension(filename: str, allowed: list[str]) -> None:
    """Validate an extension only when an explicit allow-list is configured.

    The default policy is ``*`` so documents, images, archives, slides, audio and
    video files can all be uploaded. An administrator can still restrict the list
    by changing the setting to values such as ``pdf,docx,png``.
    """
    normalized = {item.strip().lower().lstrip(".") for item in allowed if item.strip()}
    if not normalized or "*" in normalized or "all" in normalized:
        return

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in normalized:
        shown = ext or "بدون امتداد"
        raise AppError(f"Extension .{shown} is not allowed", "INVALID_EXTENSION", 422)
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_page_count(page_count: int, min_pages: int) -> None:
    if page_count < min_pages:
        raise AppError(f"PDF must contain at least {min_pages} page(s)", "PAGE_COUNT_TOO_LOW", 422)

"""Validation helpers for arbitrary user-uploaded files."""
import hashlib
from dataclasses import dataclass

from app.core.errors import AppError


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


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_page_count(page_count: int, min_pages: int) -> None:
    if page_count < min_pages:
        raise AppError(f"PDF must contain at least {min_pages} page(s)", "PAGE_COUNT_TOO_LOW", 422)

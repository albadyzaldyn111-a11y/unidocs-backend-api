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
ZIP_MAGIC = b"PK"
OLE_MAGIC = b"\xd0\xcf\x11\xe0"
MEDIA_MAGIC_PREFIXES = (b"\xff\xd8\xff", b"\x89PNG", b"GIF8", b"RIFF", b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x1cftyp")
TEXT_EXTENSIONS = {"txt", "md", "csv", "rtf", "html", "htm", "xml", "json"}
ARCHIVE_DOCUMENT_EXTENSIONS = {"docx", "xlsx", "pptx", "odt", "ods", "odp"}
OLE_DOCUMENT_EXTENSIONS = {"doc", "xls", "ppt"}


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


def validate_magic_bytes(header: bytes, extension: str) -> None:
    ext = extension.lower().lstrip(".")
    if any(header.startswith(prefix) for prefix in MEDIA_MAGIC_PREFIXES):
        raise AppError("Images, audio and video files are not allowed", "MEDIA_FILE_NOT_ALLOWED", 422)
    if ext == "pdf" and not header.startswith(PDF_MAGIC):
        raise AppError("File is not a valid PDF", "INVALID_FILE_TYPE", 422)
    if ext in ARCHIVE_DOCUMENT_EXTENSIONS and not header.startswith(ZIP_MAGIC):
        raise AppError("Document container is invalid", "INVALID_FILE_TYPE", 422)
    if ext in OLE_DOCUMENT_EXTENSIONS and not header.startswith(OLE_MAGIC):
        raise AppError("Legacy document container is invalid", "INVALID_FILE_TYPE", 422)
    if ext == "rtf" and not header.startswith(b"{\\rtf"):
        raise AppError("RTF document is invalid", "INVALID_FILE_TYPE", 422)
    if ext in TEXT_EXTENSIONS - {"rtf"}:
        try:
            header.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AppError("Text document encoding is invalid", "INVALID_FILE_TYPE", 422) from exc


def validate_extension(filename: str, allowed: list[str]) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed:
        raise AppError(f"Extension .{ext} is not allowed", "INVALID_EXTENSION", 422)


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_page_count(page_count: int, min_pages: int) -> None:
    if page_count < min_pages:
        raise AppError(f"PDF must contain at least {min_pages} page(s)", "PAGE_COUNT_TOO_LOW", 422)

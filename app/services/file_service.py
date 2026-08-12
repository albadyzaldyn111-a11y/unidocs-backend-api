import io
<<<<<<< HEAD
=======
import mimetypes
import re
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import FileStatus
from app.models.file import File
from app.repositories.file_repository import FileRepository
from app.repositories.misc_repositories import SettingsRepository
from app.repositories.taxonomy_repository import TaxonomyRepository
from app.services.audit_service import AuditService
from app.services.file_validation import (
    compute_sha256,
    validate_extension,
    validate_magic_bytes,
    validate_page_count,
    validate_size,
)
from app.storage.factory import get_storage


class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.files = FileRepository(db)
        self.taxonomy = TaxonomyRepository(db)
        self.settings = SettingsRepository(db)
        self.audit = AuditService(db)
        self.storage = get_storage()

    def upload(
        self,
        *,
        uploader_id: str,
        university_id: str,
        subject_id: str,
        title: str,
        description: str | None,
        filename: str,
        raw_bytes: bytes,
<<<<<<< HEAD
=======
        mime_type: str | None = None,
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
    ) -> File:
        subject = self.taxonomy.get_subject(subject_id, university_id)
        if not subject:
            raise AppError("Subject not found for this university", "SUBJECT_NOT_FOUND", 404)

        settings = self.settings.get_all()
        max_mb = int(settings["max_file_size_mb"])
        allowed = settings["allowed_extensions"].split(",")

        validate_extension(filename, allowed)
        validate_size(len(raw_bytes), max_mb)
        validate_magic_bytes(raw_bytes[:5])

<<<<<<< HEAD
        if settings.get("page_count_check_enabled") == "true":
=======
        extension = self._extension(filename)
        if settings.get("page_count_check_enabled") == "true" and extension == "pdf":
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
            page_count = self._count_pdf_pages(raw_bytes)
            validate_page_count(page_count, int(settings["min_page_count"]))

        file_hash = compute_sha256(raw_bytes)
<<<<<<< HEAD

=======
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
        existing = self.files.get_by_hash(file_hash, university_id)
        if existing:
            raise AppError("This exact file already exists in the library", "DUPLICATE_FILE", 409)

<<<<<<< HEAD
        storage_key = f"{university_id}/{file_hash}.pdf"
=======
        storage_key = self._storage_key(university_id, file_hash, filename)
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
        self.storage.save(storage_key, io.BytesIO(raw_bytes))

        file_obj = self.files.create(
            university_id=university_id,
            subject_id=subject_id,
            uploader_id=uploader_id,
            title=title,
            description=description,
<<<<<<< HEAD
=======
            original_filename=self._safe_filename(filename),
            mime_type=self._normalize_mime_type(mime_type, filename),
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
            storage_key=storage_key,
            file_hash=file_hash,
            file_size_bytes=len(raw_bytes),
            status=FileStatus.PENDING,
            version_number=1,
        )
        self.audit.log(uploader_id, "UPLOAD_FILE", "file", file_obj.id, title)
        self.db.commit()
        return file_obj

    def upload_new_version(
        self,
        *,
        uploader_id: str,
        university_id: str,
        parent_file_id: str,
        filename: str,
        raw_bytes: bytes,
<<<<<<< HEAD
=======
        mime_type: str | None = None,
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
    ) -> File:
        parent = self.files.get(parent_file_id, university_id)
        if not parent:
            raise AppError("Original file not found", "FILE_NOT_FOUND", 404)
        if parent.uploader_id != uploader_id:
            raise AppError("Only the original uploader can add a new version", "FORBIDDEN", 403)

        settings = self.settings.get_all()
        validate_extension(filename, settings["allowed_extensions"].split(","))
        validate_size(len(raw_bytes), int(settings["max_file_size_mb"]))
        validate_magic_bytes(raw_bytes[:5])

        file_hash = compute_sha256(raw_bytes)
        if self.files.get_by_hash(file_hash, university_id):
            raise AppError("This exact file already exists in the library", "DUPLICATE_FILE", 409)

<<<<<<< HEAD
        storage_key = f"{university_id}/{file_hash}.pdf"
=======
        storage_key = self._storage_key(university_id, file_hash, filename)
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
        self.storage.save(storage_key, io.BytesIO(raw_bytes))

        new_version = self.files.create(
            university_id=university_id,
            subject_id=parent.subject_id,
            uploader_id=uploader_id,
            title=parent.title,
            description=parent.description,
<<<<<<< HEAD
=======
            original_filename=self._safe_filename(filename),
            mime_type=self._normalize_mime_type(mime_type, filename),
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
            storage_key=storage_key,
            file_hash=file_hash,
            file_size_bytes=len(raw_bytes),
            status=FileStatus.PENDING,
            version_number=parent.version_number + 1,
            parent_file_id=parent.id,
        )
        self.audit.log(uploader_id, "UPLOAD_NEW_VERSION", "file", new_version.id, f"parent={parent.id}")
        self.db.commit()
        return new_version

    def register_view(self, file_id: str, university_id: str) -> File:
        file_obj = self._get_visible_or_404(file_id, university_id)
        file_obj.views_count += 1
        self.db.commit()
        return file_obj

    def register_download(self, file_id: str, university_id: str, user_id: str | None = None) -> File:
        file_obj = self._get_visible_or_404(file_id, university_id)
        file_obj.downloads_count += 1

<<<<<<< HEAD
        from datetime import datetime, timezone

=======
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
        from app.models.misc import DownloadLog

        self.db.add(
            DownloadLog(
                file_id=file_obj.id,
                user_id=user_id,
                university_id=university_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.db.commit()
        return file_obj

    def open_stream(self, file_obj: File):
        return self.storage.open(file_obj.storage_key)

    def _get_visible_or_404(self, file_id: str, university_id: str) -> File:
        file_obj = self.files.get(file_id, university_id)
        if not file_obj or file_obj.status not in (FileStatus.APPROVED, FileStatus.ARCHIVED):
            raise AppError("File not found", "FILE_NOT_FOUND", 404)
        return file_obj

    @staticmethod
<<<<<<< HEAD
=======
    def _safe_filename(filename: str) -> str:
        cleaned = re.sub(r"[^\w.()\- ]+", "_", (filename or "upload").strip())
        return cleaned[:512] or "upload"

    @staticmethod
    def _extension(filename: str) -> str:
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    @classmethod
    def _storage_key(cls, university_id: str, file_hash: str, filename: str) -> str:
        extension = cls._extension(filename)
        return f"{university_id}/{file_hash}{('.' + extension) if extension else ''}"

    @staticmethod
    def _normalize_mime_type(mime_type: str | None, filename: str) -> str:
        candidate = (mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream").split(";", 1)[0]
        return candidate if re.fullmatch(r"[\w.+-]+/[\w.+-]+", candidate) else "application/octet-stream"

    @staticmethod
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
    def _count_pdf_pages(raw_bytes: bytes) -> int:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(raw_bytes))
        return len(reader.pages)

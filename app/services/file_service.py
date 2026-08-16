import io
import logging
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


logger = logging.getLogger("unidocs.files")


class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.files = FileRepository(db)
        self.taxonomy = TaxonomyRepository(db)
        self.settings = SettingsRepository(db)
        self.audit = AuditService(db)
        self.storage_error: Exception | None = None
        try:
            self.storage = get_storage()
        except Exception as exc:
            logger.exception("File storage is not configured or unavailable")
            self.storage = None
            self.storage_error = exc

    def upload(
        self,
        *,
        uploader_id: str,
        university_id: str,
        subject_id: str,
        title: str,
        description: str | None,
        filename: str,
        mime_type: str | None,
        raw_bytes: bytes,
    ) -> File:
        subject = self.taxonomy.get_subject(subject_id, university_id)
        if not subject:
            raise AppError("Subject not found for this university", "SUBJECT_NOT_FOUND", 404)

        settings = self.settings.get_all()
        max_mb = int(settings["max_file_size_mb"])
        allowed = [item.strip().lower().lstrip(".") for item in settings["allowed_extensions"].split(",") if item.strip()]
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        validate_extension(filename, allowed)
        validate_size(len(raw_bytes), max_mb)
        validate_magic_bytes(raw_bytes[:16], extension)

        if settings.get("page_count_check_enabled") == "true":
            page_count = self._count_pdf_pages(raw_bytes)
            validate_page_count(page_count, int(settings["min_page_count"]))

        file_hash = compute_sha256(raw_bytes)

        existing = self.files.get_by_hash(file_hash, university_id)
        if existing:
            raise AppError("This exact file already exists in the library", "DUPLICATE_FILE", 409)

        storage_key = f"{university_id}/{file_hash}.{extension or 'bin'}"
        try:
            self._require_storage().save(storage_key, io.BytesIO(raw_bytes))
        except Exception as exc:
            logger.exception("Storage upload failed for key=%s", storage_key)
            detail = str(exc).replace("\n", " ")[:240]
            raise AppError(f"File storage is temporarily unavailable: {detail}", "STORAGE_UNAVAILABLE", 503) from exc

        file_obj = self.files.create(
            university_id=university_id,
            subject_id=subject_id,
            uploader_id=uploader_id,
            title=title,
            description=description,
            original_filename=filename,
            mime_type=mime_type or "application/octet-stream",
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
        mime_type: str | None,
        raw_bytes: bytes,
    ) -> File:
        parent = self.files.get(parent_file_id, university_id)
        if not parent:
            raise AppError("Original file not found", "FILE_NOT_FOUND", 404)
        if parent.uploader_id != uploader_id:
            raise AppError("Only the original uploader can add a new version", "FORBIDDEN", 403)

        settings = self.settings.get_all()
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        allowed = [item.strip().lower().lstrip(".") for item in settings["allowed_extensions"].split(",") if item.strip()]
        validate_extension(filename, allowed)
        validate_size(len(raw_bytes), int(settings["max_file_size_mb"]))
        validate_magic_bytes(raw_bytes[:16], extension)

        file_hash = compute_sha256(raw_bytes)
        if self.files.get_by_hash(file_hash, university_id):
            raise AppError("This exact file already exists in the library", "DUPLICATE_FILE", 409)

        storage_key = f"{university_id}/{file_hash}.{extension or 'bin'}"
        try:
            self._require_storage().save(storage_key, io.BytesIO(raw_bytes))
        except Exception as exc:
            logger.exception("Storage upload failed for version key=%s", storage_key)
            detail = str(exc).replace("\n", " ")[:240]
            raise AppError(f"File storage is temporarily unavailable: {detail}", "STORAGE_UNAVAILABLE", 503) from exc

        new_version = self.files.create(
            university_id=university_id,
            subject_id=parent.subject_id,
            uploader_id=uploader_id,
            title=parent.title,
            description=parent.description,
            original_filename=filename,
            mime_type=mime_type or "application/octet-stream",
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

    def register_view(self, file_id: str, university_id: str, viewer_id: str | None = None) -> File:
        file_obj = self._get_visible_or_404(file_id, university_id, viewer_id)
        file_obj.views_count += 1
        self.db.commit()
        return file_obj

    def register_download(self, file_id: str, university_id: str, user_id: str | None = None) -> File:
        file_obj = self._get_visible_or_404(file_id, university_id, user_id)
        file_obj.downloads_count += 1

        from datetime import datetime, timezone

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
        return self._require_storage().open(file_obj.storage_key)

    def _require_storage(self):
        if self.storage is None:
            detail = str(self.storage_error).replace("\n", " ")[:240] if self.storage_error else "provider is not configured"
            raise AppError(f"File storage is temporarily unavailable: {detail}", "STORAGE_UNAVAILABLE", 503)
        return self.storage

    def _get_visible_or_404(self, file_id: str, university_id: str, viewer_id: str | None = None) -> File:
        file_obj = self.files.get(file_id, university_id)
        if not file_obj:
            raise AppError("File not found", "FILE_NOT_FOUND", 404)

        # Visible if approved/archived OR if the viewer is the uploader
        is_visible = file_obj.status in (FileStatus.APPROVED, FileStatus.ARCHIVED)
        if not is_visible and viewer_id and file_obj.uploader_id == viewer_id:
            is_visible = True

        if not is_visible:
            raise AppError("File not found", "FILE_NOT_FOUND", 404)
        return file_obj

    @staticmethod
    def _count_pdf_pages(raw_bytes: bytes) -> int:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(raw_bytes))
        return len(reader.pages)

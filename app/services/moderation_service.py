from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.enums import FileStatus, NotificationType
from app.repositories.file_repository import FileRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.storage.factory import get_storage


class ModerationService:
    def __init__(self, db: Session):
        self.db = db
        self.files = FileRepository(db)
        self.audit = AuditService(db)
        self.notifications = NotificationService(db)
        self.storage = get_storage()
        self.settings = get_settings()

    def lock(self, file_id: str, university_id: str, moderator_id: str):
        file_obj = self._get_or_404(file_id, university_id)
        now = datetime.now(timezone.utc)

        if file_obj.review_locked_by and file_obj.review_locked_by != moderator_id and file_obj.review_locked_at:
            lock_expires = file_obj.review_locked_at + timedelta(minutes=self.settings.REVIEW_LOCK_MINUTES)
            if lock_expires.tzinfo is None:
                lock_expires = lock_expires.replace(tzinfo=timezone.utc)
            if now < lock_expires:
                raise AppError(
                    "This file is currently under review by another moderator.",
                    "FILE_LOCKED",
                    409,
                )

        file_obj.review_locked_by = moderator_id
        file_obj.review_locked_at = now
        self.db.commit()
        return file_obj

    def approve(self, file_id: str, university_id: str, moderator_id: str):
        file_obj = self._get_or_404(file_id, university_id)
        file_obj.status = FileStatus.APPROVED
        file_obj.review_locked_by = None
        file_obj.review_locked_at = None

        # If this is a new version of an existing approved file, archive the old one.
        if file_obj.parent_file_id:
            parent = self.files.get(file_obj.parent_file_id, university_id)
            if parent and parent.status == FileStatus.APPROVED:
                parent.status = FileStatus.ARCHIVED
                self.notifications.notify(
                    parent.uploader_id,
                    NotificationType.NEW_VERSION_APPROVED,
                    "New version approved",
                    f"A new version of '{parent.title}' has been approved.",
                    "file",
                    file_obj.id,
                )

        self.notifications.notify(
            file_obj.uploader_id,
            NotificationType.FILE_APPROVED,
            "File approved",
            f"Your file '{file_obj.title}' has been approved.",
            "file",
            file_obj.id,
        )
        self.audit.log(moderator_id, "APPROVE_FILE", "file", file_obj.id)
        self.db.commit()
        return file_obj

    def reject(self, file_id: str, university_id: str, moderator_id: str, reason: str):
        if not reason or not reason.strip():
            raise AppError("A rejection reason is required", "REASON_REQUIRED", 422)

        file_obj = self._get_or_404(file_id, university_id)
        file_obj.status = FileStatus.REJECTED
        file_obj.rejection_reason = reason
        file_obj.review_locked_by = None
        file_obj.review_locked_at = None

        self.notifications.notify(
            file_obj.uploader_id,
            NotificationType.FILE_REJECTED,
            "File rejected",
            reason,
            "file",
            file_obj.id,
        )
        self.audit.log(moderator_id, "REJECT_FILE", "file", file_obj.id, reason)
        self.db.commit()
        return file_obj

    def delete(self, file_id: str, university_id: str, moderator_id: str):
        file_obj = self._get_or_404(file_id, university_id)
        try:
            self.storage.delete(file_obj.storage_key)
        except Exception:
            pass  # storage cleanup failure should not block the audit-critical delete
        self.audit.log(moderator_id, "DELETE_FILE", "file", file_obj.id, "violating content")
        self.db.delete(file_obj)
        self.db.commit()

    def _get_or_404(self, file_id: str, university_id: str):
        file_obj = self.files.get(file_id, university_id)
        if not file_obj:
            raise AppError("File not found", "FILE_NOT_FOUND", 404)
        return file_obj

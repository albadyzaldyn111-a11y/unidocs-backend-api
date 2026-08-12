from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import UploadRequestStatus
from app.models.misc import Notification, SystemSetting, UploadRequest


class UploadRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> UploadRequest:
        req = UploadRequest(**kwargs)
        self.db.add(req)
        self.db.flush()
        return req

    def get(self, request_id: str, university_id: str) -> UploadRequest | None:
        return self.db.scalar(
            select(UploadRequest).where(
                UploadRequest.id == request_id, UploadRequest.university_id == university_id
            )
        )

    def list_by_university(
        self, university_id: str, status: UploadRequestStatus | None = None
    ) -> list[UploadRequest]:
        stmt = select(UploadRequest).where(UploadRequest.university_id == university_id)
        if status:
            stmt = stmt.where(UploadRequest.status == status)
        return list(self.db.scalars(stmt.order_by(UploadRequest.created_at.desc())))

    def list_by_user(self, user_id: str) -> list[UploadRequest]:
        return list(
            self.db.scalars(
                select(UploadRequest).where(UploadRequest.user_id == user_id).order_by(UploadRequest.created_at.desc())
            )
        )

    def has_pending(self, user_id: str) -> bool:
        return (
            self.db.scalar(
                select(UploadRequest).where(
                    UploadRequest.user_id == user_id, UploadRequest.status == UploadRequestStatus.PENDING
                )
            )
            is not None
        )


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: str, page: int = 1, limit: int = 20) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def get(self, notification_id: str, user_id: str) -> Notification | None:
        return self.db.scalar(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )

    def mark_all_read(self, user_id: str) -> None:
        notifications = self.db.scalars(
            select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        for n in notifications:
            n.is_read = True


class SettingsRepository:
    DEFAULTS = {
        "max_file_size_mb": "50",
<<<<<<< HEAD
        "allowed_extensions": "pdf",
=======
        "allowed_extensions": "*",
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
        "page_count_check_enabled": "false",
        "min_page_count": "1",
        "review_lock_minutes": "15",
        "email_notifications_enabled": "false",
    }

    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> str:
        setting = self.db.get(SystemSetting, key)
        return setting.value if setting else self.DEFAULTS.get(key, "")

    def get_all(self) -> dict[str, str]:
        rows = {s.key: s.value for s in self.db.scalars(select(SystemSetting))}
        merged = dict(self.DEFAULTS)
        merged.update(rows)
        return merged

    def set(self, key: str, value: str) -> None:
        setting = self.db.get(SystemSetting, key)
        if setting:
            setting.value = value
        else:
            self.db.add(SystemSetting(key=key, value=value))

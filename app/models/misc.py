from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import NotificationType, UploadRequestStatus


class UploadRequest(Base, UUIDMixin, TimestampMixin):
    """A Student requests to become a Verified Uploader."""

    __tablename__ = "upload_requests"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[UploadRequestStatus] = mapped_column(
        Enum(UploadRequestStatus), default=UploadRequestStatus.PENDING, index=True
    )
    reviewed_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str] = mapped_column(Text, nullable=True)


class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=True)
    related_entity_type: Mapped[str] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[str] = mapped_column(String(36), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class DownloadLog(Base, UUIDMixin):
    __tablename__ = "download_logs"

    file_id: Mapped[str] = mapped_column(ForeignKey("files.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SystemSetting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)

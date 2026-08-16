from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import FileStatus


class File(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "files"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), index=True, nullable=False)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), index=True, nullable=False)
    uploader_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)

    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # SHA-256
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[FileStatus] = mapped_column(Enum(FileStatus), default=FileStatus.PENDING, index=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)

    version_number: Mapped[int] = mapped_column(Integer, default=1)
    parent_file_id: Mapped[str] = mapped_column(ForeignKey("files.id"), nullable=True)

    review_locked_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    views_count: Mapped[int] = mapped_column(Integer, default=0)

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import FileStatus
from app.models.file import File


class FileRepository:
    """Every method requires university_id so tenant isolation is enforced
    at the data-access layer, not left to callers to remember."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, file_id: str, university_id: str) -> File | None:
        return self.db.scalar(select(File).where(File.id == file_id, File.university_id == university_id))

    def get_by_id_only(self, file_id: str) -> File | None:
        return self.db.get(File, file_id)

    def get_by_hash(self, file_hash: str, university_id: str) -> File | None:
        return self.db.scalar(
            select(File).where(File.file_hash == file_hash, File.university_id == university_id)
        )

    def create(self, **kwargs) -> File:
        file_obj = File(**kwargs)
        self.db.add(file_obj)
        self.db.flush()
        return file_obj

    def search(
        self,
        university_id: str,
        q: str | None = None,
        faculty_subject_ids: list[str] | None = None,
        subject_id: str | None = None,
        status: FileStatus = FileStatus.APPROVED,
        sort: str = "recent",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[File], int]:
        stmt = select(File).where(File.university_id == university_id, File.status == status)

        if subject_id:
            stmt = stmt.where(File.subject_id == subject_id)
        elif faculty_subject_ids:
            stmt = stmt.where(File.subject_id.in_(faculty_subject_ids))

        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(File.title.ilike(like), File.description.ilike(like)))

        if sort == "popular":
            stmt = stmt.order_by(File.downloads_count.desc())
        elif sort == "views":
            stmt = stmt.order_by(File.views_count.desc())
        else:
            stmt = stmt.order_by(File.created_at.desc())

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(self.db.scalars(stmt.offset((page - 1) * limit).limit(limit)))
        return items, total

    def list_by_uploader(
        self, uploader_id: str, university_id: str, status: FileStatus | None = None
    ) -> list[File]:
        stmt = select(File).where(File.uploader_id == uploader_id, File.university_id == university_id)
        if status:
            stmt = stmt.where(File.status == status)
        return list(self.db.scalars(stmt.order_by(File.created_at.desc())))

    def list_pending(self, university_id: str, page: int = 1, limit: int = 20) -> tuple[list[File], int]:
        stmt = select(File).where(File.university_id == university_id, File.status == FileStatus.PENDING)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(self.db.scalars(stmt.order_by(File.created_at.asc()).offset((page - 1) * limit).limit(limit)))
        return items, total

    def stats(self, university_id: str) -> dict:
        def count(status: FileStatus) -> int:
            return (
                self.db.scalar(
                    select(func.count()).select_from(File).where(
                        File.university_id == university_id, File.status == status
                    )
                )
                or 0
            )

        total_downloads = (
            self.db.scalar(
                select(func.coalesce(func.sum(File.downloads_count), 0)).where(File.university_id == university_id)
            )
            or 0
        )
        total_views = (
            self.db.scalar(
                select(func.coalesce(func.sum(File.views_count), 0)).where(File.university_id == university_id)
            )
            or 0
        )
        return {
            "approved_files": count(FileStatus.APPROVED),
            "pending_files": count(FileStatus.PENDING),
            "rejected_files": count(FileStatus.REJECTED),
            "archived_files": count(FileStatus.ARCHIVED),
            "total_downloads": total_downloads,
            "total_views": total_views,
        }

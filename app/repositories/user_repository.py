from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        self.db.flush()
        return user

    def list_by_university(self, university_id: str, page: int = 1, limit: int = 20) -> tuple[list[User], int]:
        return self.list_admin(page=page, limit=limit, university_id=university_id)

    def list_admin(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        university_id: str | None = None,
    ) -> tuple[list[User], int]:
        filters = []
        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(or_(User.full_name.ilike(term), User.email.ilike(term)))
        if role is not None:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if university_id:
            filters.append(User.university_id == university_id)

        base = select(User).where(*filters).order_by(User.created_at.desc())
        items = self.db.scalars(base.offset((page - 1) * limit).limit(limit)).all()
        total = self.db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
        return list(items), total

    def active_ids_by_university(self, university_id: str) -> list[str]:
        return list(
            self.db.scalars(
                select(User.id).where(User.university_id == university_id, User.is_active.is_(True))
            )
        )

    def count_by_university(self, university_id: str) -> int:
        return self.db.scalar(select(func.count()).select_from(User).where(User.university_id == university_id)) or 0

    def count_all(self) -> int:
        return self.db.scalar(select(func.count()).select_from(User)) or 0

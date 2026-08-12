from sqlalchemy import func, select
from sqlalchemy.orm import Session

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
        base = select(User).where(User.university_id == university_id)
        items = self.db.scalars(base.offset((page - 1) * limit).limit(limit)).all()
        total = self.count_by_university(university_id)
        return list(items), total

    def count_by_university(self, university_id: str) -> int:
        return (
            self.db.scalar(select(func.count()).select_from(User).where(User.university_id == university_id)) or 0
        )

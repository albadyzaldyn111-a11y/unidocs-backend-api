from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.taxonomy import Department, Faculty, Level, Subject, University


class TaxonomyRepository:
    """All reads are scoped so a caller can never see another university's
    academic structure by guessing IDs."""

    def __init__(self, db: Session):
        self.db = db

    def list_universities(self) -> list[University]:
        return list(self.db.scalars(select(University).where(University.is_active.is_(True))))

    def list_faculties(self, university_id: str) -> list[Faculty]:
        return list(
            self.db.scalars(
                select(Faculty).where(Faculty.university_id == university_id, Faculty.is_active.is_(True))
            )
        )

    def list_departments(self, faculty_id: str, university_id: str) -> list[Department]:
        return list(
            self.db.scalars(
                select(Department).where(
                    Department.faculty_id == faculty_id,
                    Department.university_id == university_id,
                    Department.is_active.is_(True),
                )
            )
        )

    def list_levels(self, department_id: str, university_id: str) -> list[Level]:
        return list(
            self.db.scalars(
                select(Level)
                .where(Level.department_id == department_id, Level.university_id == university_id)
                .order_by(Level.order_index)
            )
        )

    def list_subjects(self, level_id: str, university_id: str) -> list[Subject]:
        return list(
            self.db.scalars(select(Subject).where(Subject.level_id == level_id, Subject.university_id == university_id))
        )

    def get_subject(self, subject_id: str, university_id: str | None) -> Subject | None:
        stmt = select(Subject).where(Subject.id == subject_id)
        if university_id:
            stmt = stmt.where(Subject.university_id == university_id)
        return self.db.scalar(stmt)

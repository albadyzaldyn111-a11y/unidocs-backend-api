from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class University(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "universities"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    faculties: Mapped[list["Faculty"]] = relationship(back_populates="university", cascade="all, delete-orphan")


class Faculty(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "faculties"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    university: Mapped["University"] = relationship(back_populates="faculties")
    departments: Mapped[list["Department"]] = relationship(back_populates="faculty", cascade="all, delete-orphan")


class Department(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "departments"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), index=True, nullable=False)
    faculty_id: Mapped[str] = mapped_column(ForeignKey("faculties.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    faculty: Mapped["Faculty"] = relationship(back_populates="departments")
    levels: Mapped[list["Level"]] = relationship(back_populates="department", cascade="all, delete-orphan")


class Level(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "levels"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), index=True, nullable=False)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    department: Mapped["Department"] = relationship(back_populates="levels")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="level", cascade="all, delete-orphan")


class Subject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subjects"

    university_id: Mapped[str] = mapped_column(ForeignKey("universities.id"), index=True, nullable=False)
    level_id: Mapped[str] = mapped_column(ForeignKey("levels.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=True)

    level: Mapped["Level"] = relationship(back_populates="subjects")

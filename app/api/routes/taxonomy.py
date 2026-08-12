from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.repositories.taxonomy_repository import TaxonomyRepository
from app.schemas.taxonomy import DepartmentOut, FacultyOut, LevelOut, SubjectOut, UniversityOut

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])


@router.get("/universities", response_model=list[UniversityOut])
def list_universities(db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_universities()


@router.get("/universities/{university_id}/faculties", response_model=list[FacultyOut])
def list_faculties(university_id: str, db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_faculties(university_id)


@router.get("/faculties/{faculty_id}/departments", response_model=list[DepartmentOut])
def list_departments(faculty_id: str, university_id: str, db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_departments(faculty_id, university_id)


@router.get("/departments/{department_id}/levels", response_model=list[LevelOut])
def list_levels(department_id: str, university_id: str, db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_levels(department_id, university_id)


@router.get("/levels/{level_id}/subjects", response_model=list[SubjectOut])
def list_subjects(level_id: str, university_id: str, db: Session = Depends(get_db)):
    return TaxonomyRepository(db).list_subjects(level_id, university_id)

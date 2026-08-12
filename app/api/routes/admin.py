from sqlalchemy import select
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import CurrentUser, require_admin
from app.models.enums import UserRole
from app.models.misc import AuditLog
from app.models.taxonomy import Department, Faculty, Level, Subject, University
from app.repositories.misc_repositories import SettingsRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_taxonomy import (
    DepartmentCreate,
    FacultyCreate,
    LevelCreate,
    SubjectCreate,
    UniversityCreate,
)
from app.schemas.auth import UserOut
from app.schemas.misc import AdminStatsOut, SettingUpdate
from app.schemas.taxonomy import DepartmentOut, FacultyOut, LevelOut, SubjectOut, UniversityOut
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsOut)
def stats(current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return AdminService(db).stats(current_user.university_id)


@router.get("/users", response_model=list[UserOut])
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, _ = UserRepository(db).list_by_university(current_user.university_id, page, limit)
    return items


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    from app.core.errors import AppError

    user = UserRepository(db).get_by_id(user_id)
    if not user or user.university_id != current_user.university_id:
        raise AppError("User not found", "USER_NOT_FOUND", 404)
    return user


@router.post("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    return AdminService(db).set_user_active(current_user.id, user_id, current_user.university_id, False)


@router.post("/users/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return AdminService(db).set_user_active(current_user.id, user_id, current_user.university_id, True)


@router.post("/users/{user_id}/role/{role}", response_model=UserOut)
def change_role(
    user_id: str, role: UserRole, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    return AdminService(db).set_user_role(current_user.id, user_id, current_user.university_id, role)


@router.get("/audit-log")
def audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = db.scalars(stmt).all()
    return [
        {
            "id": r.id,
            "actor_id": r.actor_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "details": r.details,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/settings")
def get_settings_values(current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return SettingsRepository(db).get_all()


@router.put("/settings/{key}")
def update_setting(
    key: str,
    payload: SettingUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    AdminService(db).update_setting(current_user.id, key, payload.value)
    return {"success": True, "message": "Setting updated"}


# --- Academic structure management -----------------------------------------
# Adding a new university only ever requires inserting rows through these
# endpoints — never a code change, per the multi-tenancy requirement.


@router.post("/universities", response_model=UniversityOut, status_code=201)
def create_university(
    payload: UniversityCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    uni = University(name=payload.name, name_en=payload.name_en, city=payload.city)
    db.add(uni)
    db.flush()
    AuditService(db).log(current_user.id, "CREATE_UNIVERSITY", "university", uni.id, payload.name)
    db.commit()
    return uni


@router.post("/faculties", response_model=FacultyOut, status_code=201)
def create_faculty(
    payload: FacultyCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    faculty = Faculty(university_id=payload.university_id, name=payload.name, name_en=payload.name_en)
    db.add(faculty)
    db.flush()
    AuditService(db).log(current_user.id, "CREATE_FACULTY", "faculty", faculty.id, payload.name)
    db.commit()
    return faculty


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    dept = Department(
        university_id=payload.university_id,
        faculty_id=payload.faculty_id,
        name=payload.name,
        name_en=payload.name_en,
    )
    db.add(dept)
    db.flush()
    AuditService(db).log(current_user.id, "CREATE_DEPARTMENT", "department", dept.id, payload.name)
    db.commit()
    return dept


@router.post("/levels", response_model=LevelOut, status_code=201)
def create_level(
    payload: LevelCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    level = Level(
        university_id=payload.university_id,
        department_id=payload.department_id,
        name=payload.name,
        name_en=payload.name_en,
        order_index=payload.order_index,
    )
    db.add(level)
    db.flush()
    AuditService(db).log(current_user.id, "CREATE_LEVEL", "level", level.id, payload.name)
    db.commit()
    return level


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(
    payload: SubjectCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    subject = Subject(
        university_id=payload.university_id,
        level_id=payload.level_id,
        name=payload.name,
        name_en=payload.name_en,
        code=payload.code,
    )
    db.add(subject)
    db.flush()
    AuditService(db).log(current_user.id, "CREATE_SUBJECT", "subject", subject.id, payload.name)
    db.commit()
    return subject

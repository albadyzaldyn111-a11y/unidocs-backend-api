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
    DepartmentUpdate,
    FacultyCreate,
    FacultyUpdate,
    LevelCreate,
    LevelUpdate,
    SubjectCreate,
    SubjectUpdate,
    UniversityCreate,
    UniversityUpdate,
    PasswordResetRequest,
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
    search: str | None = Query(default=None, max_length=120),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    university_id: str | None = Query(default=None),
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, _ = UserRepository(db).list_admin(
        page=page,
        limit=limit,
        search=search,
        role=role,
        is_active=is_active,
        university_id=university_id,
    )
    return items


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    from app.core.errors import AppError

    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise AppError("User not found", "USER_NOT_FOUND", 404)
    return user


@router.post("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    return AdminService(db).set_user_active(current_user.id, user_id, None, False)


@router.post("/users/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return AdminService(db).set_user_active(current_user.id, user_id, None, True)


@router.post("/users/{user_id}/role/{role}", response_model=UserOut)
def change_role(
    user_id: str, role: UserRole, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    return AdminService(db).set_user_role(current_user.id, user_id, None, role)


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: str,
    payload: PasswordResetRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return AdminService(db).reset_user_password(current_user.id, user_id, None, payload.new_password)


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


# --- Academic structure update/archive management --------------------------

@router.patch("/universities/{university_id}", response_model=UniversityOut)
def update_university(
    university_id: str,
    payload: UniversityUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    uni = db.get(University, university_id)
    if not uni:
        raise AppError("University not found", "UNIVERSITY_NOT_FOUND", 404)
    for field in ("name", "name_en", "city", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(uni, field, value)
    AuditService(db).log(current_user.id, "UPDATE_UNIVERSITY", "university", uni.id, uni.name)
    db.commit()
    return uni


@router.delete("/universities/{university_id}", response_model=UniversityOut)
def archive_university(
    university_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    uni = db.get(University, university_id)
    if not uni:
        raise AppError("University not found", "UNIVERSITY_NOT_FOUND", 404)
    uni.is_active = False
    for faculty in uni.faculties:
        faculty.is_active = False
        for department in faculty.departments:
            department.is_active = False
    AuditService(db).log(current_user.id, "ARCHIVE_UNIVERSITY", "university", uni.id, uni.name)
    db.commit()
    return uni


@router.patch("/faculties/{faculty_id}", response_model=FacultyOut)
def update_faculty(
    faculty_id: str,
    payload: FacultyUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    faculty = db.get(Faculty, faculty_id)
    if not faculty:
        raise AppError("Faculty not found", "FACULTY_NOT_FOUND", 404)
    for field in ("name", "name_en", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(faculty, field, value)
    AuditService(db).log(current_user.id, "UPDATE_FACULTY", "faculty", faculty.id, faculty.name)
    db.commit()
    return faculty


@router.delete("/faculties/{faculty_id}", response_model=FacultyOut)
def archive_faculty(
    faculty_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    faculty = db.get(Faculty, faculty_id)
    if not faculty:
        raise AppError("Faculty not found", "FACULTY_NOT_FOUND", 404)
    faculty.is_active = False
    for department in faculty.departments:
        department.is_active = False
    AuditService(db).log(current_user.id, "ARCHIVE_FACULTY", "faculty", faculty.id, faculty.name)
    db.commit()
    return faculty


@router.patch("/departments/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: str,
    payload: DepartmentUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    department = db.get(Department, department_id)
    if not department:
        raise AppError("Department not found", "DEPARTMENT_NOT_FOUND", 404)
    for field in ("name", "name_en", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(department, field, value)
    AuditService(db).log(current_user.id, "UPDATE_DEPARTMENT", "department", department.id, department.name)
    db.commit()
    return department


@router.delete("/departments/{department_id}", response_model=DepartmentOut)
def archive_department(
    department_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    department = db.get(Department, department_id)
    if not department:
        raise AppError("Department not found", "DEPARTMENT_NOT_FOUND", 404)
    department.is_active = False
    AuditService(db).log(current_user.id, "ARCHIVE_DEPARTMENT", "department", department.id, department.name)
    db.commit()
    return department


@router.patch("/levels/{level_id}", response_model=LevelOut)
def update_level(
    level_id: str,
    payload: LevelUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    level = db.get(Level, level_id)
    if not level:
        raise AppError("Level not found", "LEVEL_NOT_FOUND", 404)
    for field in ("name", "name_en", "order_index"):
        value = getattr(payload, field)
        if value is not None:
            setattr(level, field, value)
    AuditService(db).log(current_user.id, "UPDATE_LEVEL", "level", level.id, level.name)
    db.commit()
    return level


@router.delete("/levels/{level_id}", response_model=LevelOut)
def delete_level(
    level_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError
    from sqlalchemy.exc import IntegrityError

    level = db.get(Level, level_id)
    if not level:
        raise AppError("Level not found", "LEVEL_NOT_FOUND", 404)
    snapshot = level
    db.delete(level)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError("Level is used by files and cannot be deleted", "ENTITY_IN_USE", 409) from exc
    return snapshot


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: str,
    payload: SubjectUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError

    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppError("Subject not found", "SUBJECT_NOT_FOUND", 404)
    for field in ("name", "name_en", "code"):
        value = getattr(payload, field)
        if value is not None:
            setattr(subject, field, value)
    AuditService(db).log(current_user.id, "UPDATE_SUBJECT", "subject", subject.id, subject.name)
    db.commit()
    return subject


@router.delete("/subjects/{subject_id}", response_model=SubjectOut)
def delete_subject(
    subject_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.core.errors import AppError
    from sqlalchemy.exc import IntegrityError

    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppError("Subject not found", "SUBJECT_NOT_FOUND", 404)
    snapshot = subject
    db.delete(subject)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError("Subject is used by files and cannot be deleted", "ENTITY_IN_USE", 409) from exc
    return snapshot


@router.get("/universities", response_model=list[UniversityOut])
def admin_list_universities(current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(University).where(University.is_active == True).order_by(University.created_at.desc())).all())


@router.get("/universities/{university_id}/faculties", response_model=list[FacultyOut])
def admin_list_faculties(university_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(Faculty).where(Faculty.university_id == university_id, Faculty.is_active == True).order_by(Faculty.created_at.desc())).all())


@router.get("/faculties/{faculty_id}/departments", response_model=list[DepartmentOut])
def admin_list_departments(faculty_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(Department).where(Department.faculty_id == faculty_id, Department.is_active == True).order_by(Department.created_at.desc())).all())


@router.get("/departments/{department_id}/levels", response_model=list[LevelOut])
def admin_list_levels(department_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(Level).where(Level.department_id == department_id).order_by(Level.order_index)).all())


@router.get("/levels/{level_id}/subjects", response_model=list[SubjectOut])
def admin_list_subjects(level_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(Subject).where(Subject.level_id == level_id).order_by(Subject.name)).all())

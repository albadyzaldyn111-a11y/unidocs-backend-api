from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
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
)
from app.schemas.auth import UserOut, UserUpdate
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


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise AppError("User not found", "USER_NOT_FOUND", 404)
    
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.university_id is not None:
        user.university_id = payload.university_id
    if payload.is_active is not None:
        user.is_active = payload.is_active
    
    db.commit()
    AuditService(db).log(current_user.id, "UPDATE_USER", "user", user.id, user.email)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise AppError("User not found", "USER_NOT_FOUND", 404)
    
    if user.id == current_user.id:
        raise AppError("Cannot delete yourself", "FORBIDDEN", 403)
        
    db.delete(user)
    db.commit()
    AuditService(db).log(current_user.id, "DELETE_USER", "user", user_id, user.email)
    return {"success": True, "message": "User deleted"}


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


@router.put("/universities/{uni_id}", response_model=UniversityOut)
def update_university(
    uni_id: str,
    payload: UniversityUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    uni = db.get(University, uni_id)
    if not uni:
        raise AppError("University not found", "UNIVERSITY_NOT_FOUND", 404)
    
    if payload.name is not None:
        uni.name = payload.name
    if payload.name_en is not None:
        uni.name_en = payload.name_en
    if payload.city is not None:
        uni.city = payload.city
    if payload.is_active is not None:
        uni.is_active = payload.is_active
        
    db.commit()
    AuditService(db).log(current_user.id, "UPDATE_UNIVERSITY", "university", uni.id, uni.name)
    return uni


@router.delete("/universities/{uni_id}")
def delete_university(uni_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    uni = db.get(University, uni_id)
    if not uni:
        raise AppError("University not found", "UNIVERSITY_NOT_FOUND", 404)
    db.delete(uni)
    db.commit()
    AuditService(db).log(current_user.id, "DELETE_UNIVERSITY", "university", uni_id, uni.name)
    return {"success": True, "message": "University deleted"}


@router.post("/faculties", response_model=FacultyOut, status_code=201)
def create_faculty(
    payload: FacultyCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    university = db.get(University, payload.university_id)
    if not university:
        raise AppError("University not found", "UNIVERSITY_NOT_FOUND", 404)
    faculty = Faculty(university_id=payload.university_id, name=payload.name, name_en=payload.name_en)
    db.add(faculty)
    db.flush()
    AuditService(db).log(current_user.id, "CREATE_FACULTY", "faculty", faculty.id, payload.name)
    db.commit()
    return faculty


@router.put("/faculties/{faculty_id}", response_model=FacultyOut)
def update_faculty(
    faculty_id: str,
    payload: FacultyUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    faculty = db.get(Faculty, faculty_id)
    if not faculty:
        raise AppError("Faculty not found", "FACULTY_NOT_FOUND", 404)
    
    if payload.name is not None:
        faculty.name = payload.name
    if payload.name_en is not None:
        faculty.name_en = payload.name_en
    if payload.is_active is not None:
        faculty.is_active = payload.is_active
        
    db.commit()
    AuditService(db).log(current_user.id, "UPDATE_FACULTY", "faculty", faculty.id, faculty.name)
    return faculty


@router.delete("/faculties/{faculty_id}")
def delete_faculty(faculty_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    faculty = db.get(Faculty, faculty_id)
    if not faculty:
        raise AppError("Faculty not found", "FACULTY_NOT_FOUND", 404)
    db.delete(faculty)
    db.commit()
    AuditService(db).log(current_user.id, "DELETE_FACULTY", "faculty", faculty_id, faculty.name)
    return {"success": True, "message": "Faculty deleted"}


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    faculty = db.get(Faculty, payload.faculty_id)
    if not faculty or faculty.university_id != payload.university_id:
        raise AppError("Faculty does not belong to this university", "FACULTY_NOT_FOUND", 404)
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


@router.put("/departments/{dept_id}", response_model=DepartmentOut)
def update_department(
    dept_id: str,
    payload: DepartmentUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    dept = db.get(Department, dept_id)
    if not dept:
        raise AppError("Department not found", "DEPARTMENT_NOT_FOUND", 404)
    
    if payload.name is not None:
        dept.name = payload.name
    if payload.name_en is not None:
        dept.name_en = payload.name_en
    if payload.is_active is not None:
        dept.is_active = payload.is_active
        
    db.commit()
    AuditService(db).log(current_user.id, "UPDATE_DEPARTMENT", "department", dept.id, dept.name)
    return dept


@router.delete("/departments/{dept_id}")
def delete_department(dept_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    dept = db.get(Department, dept_id)
    if not dept:
        raise AppError("Department not found", "DEPARTMENT_NOT_FOUND", 404)
    db.delete(dept)
    db.commit()
    AuditService(db).log(current_user.id, "DELETE_DEPARTMENT", "department", dept_id, dept.name)
    return {"success": True, "message": "Department deleted"}


@router.post("/levels", response_model=LevelOut, status_code=201)
def create_level(
    payload: LevelCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    department = db.get(Department, payload.department_id)
    if not department or department.university_id != payload.university_id:
        raise AppError("Department does not belong to this university", "DEPARTMENT_NOT_FOUND", 404)
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


@router.put("/levels/{level_id}", response_model=LevelOut)
def update_level(
    level_id: str,
    payload: LevelUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    level = db.get(Level, level_id)
    if not level:
        raise AppError("Level not found", "LEVEL_NOT_FOUND", 404)
    
    if payload.name is not None:
        level.name = payload.name
    if payload.name_en is not None:
        level.name_en = payload.name_en
    if payload.order_index is not None:
        level.order_index = payload.order_index
        
    db.commit()
    AuditService(db).log(current_user.id, "UPDATE_LEVEL", "level", level.id, level.name)
    return level


@router.delete("/levels/{level_id}")
def delete_level(level_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    level = db.get(Level, level_id)
    if not level:
        raise AppError("Level not found", "LEVEL_NOT_FOUND", 404)
    db.delete(level)
    db.commit()
    AuditService(db).log(current_user.id, "DELETE_LEVEL", "level", level_id, level.name)
    return {"success": True, "message": "Level deleted"}


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(
    payload: SubjectCreate, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)
):
    level = db.get(Level, payload.level_id)
    if not level or level.university_id != payload.university_id:
        raise AppError("Level does not belong to this university", "LEVEL_NOT_FOUND", 404)
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


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: str,
    payload: SubjectUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppError("Subject not found", "SUBJECT_NOT_FOUND", 404)
    
    if payload.name is not None:
        subject.name = payload.name
    if payload.name_en is not None:
        subject.name_en = payload.name_en
    if payload.code is not None:
        subject.code = payload.code
    if payload.is_active is not None:
        subject.is_active = payload.is_active
        
    db.commit()
    AuditService(db).log(current_user.id, "UPDATE_SUBJECT", "subject", subject.id, subject.name)
    return subject


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppError("Subject not found", "SUBJECT_NOT_FOUND", 404)
    db.delete(subject)
    db.commit()
    AuditService(db).log(current_user.id, "DELETE_SUBJECT", "subject", subject_id, subject.name)
    return {"success": True, "message": "Subject deleted"}

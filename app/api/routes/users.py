from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.middleware.auth import CurrentUser, get_current_user
from app.models.file import File
from app.models.misc import DownloadLog
from app.repositories.taxonomy_repository import TaxonomyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ChangePasswordRequest, DeleteAccountRequest, ProfileUpdate, UserOut
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(current_user.id)
    if not user:
        raise AppError("User not found", "USER_NOT_FOUND", 404)
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.university_id is not None:
        active_universities = {u.id for u in TaxonomyRepository(db).list_universities()}
        if payload.university_id not in active_universities:
            raise AppError("Invalid university", "INVALID_UNIVERSITY", 422)
        user.university_id = payload.university_id
    AuditService(db).log(user.id, "UPDATE_PROFILE", "user", user.id)
    db.commit()
    return user


@router.post("/me/change-password")
def change_my_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(current_user.id)
    if not user or not verify_password(payload.current_password, user.password_hash):
        raise AppError("Current password is incorrect", "INVALID_CURRENT_PASSWORD", 400)
    if payload.current_password == payload.new_password:
        raise AppError("New password must be different", "PASSWORD_NOT_CHANGED", 422)
    user.password_hash = hash_password(payload.new_password)
    AuditService(db).log(user.id, "CHANGE_OWN_PASSWORD", "user", user.id)
    db.commit()
    return {"success": True, "message": "Password changed successfully"}


@router.delete("/me")
def delete_my_account(
    payload: DeleteAccountRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(current_user.id)
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppError("Password is incorrect", "INVALID_PASSWORD", 400)
    user.is_active = False
    AuditService(db).log(user.id, "DELETE_ACCOUNT", "user", user.id)
    db.commit()
    return {"success": True, "message": "Account deactivated"}


@router.get("/me/downloads")
def my_download_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(DownloadLog, File)
        .join(File, File.id == DownloadLog.file_id)
        .where(DownloadLog.user_id == current_user.id, DownloadLog.university_id == current_user.university_id)
        .order_by(DownloadLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "file_id": file.id,
            "title": file.title,
            "downloaded_at": log.created_at,
        }
        for log, file in rows
    ]

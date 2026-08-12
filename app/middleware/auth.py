"""
FastAPI dependencies enforcing authentication and RBAC.
This is the real security boundary — Flutter route guards are UX only.
"""
from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import decode_token
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository


@dataclass
class CurrentUser:
    id: str
    role: UserRole
    university_id: str


def get_current_user(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError("Authentication required", "UNAUTHENTICATED", 401)

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AppError("Invalid or expired token", "INVALID_TOKEN", 401) from exc

    user_id = payload.get("sub")
    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise AppError("User not found or inactive", "UNAUTHENTICATED", 401)

    return CurrentUser(id=user.id, role=user.role, university_id=user.university_id)


def get_optional_user(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> CurrentUser | None:
    """Same as get_current_user but returns None instead of raising —
    used for endpoints visitors may access anonymously while still
    attributing the action when a valid token is present (e.g. downloads)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        return get_current_user(authorization=authorization, db=db)
    except AppError:
        return None


def require_roles(*roles: UserRole):
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise AppError("You do not have permission to perform this action", "FORBIDDEN", 403)
        return current_user

    return dependency


require_student_or_above = require_roles(
    UserRole.STUDENT, UserRole.VERIFIED_UPLOADER, UserRole.MODERATOR, UserRole.ADMINISTRATOR
)
require_uploader = require_roles(
    UserRole.VERIFIED_UPLOADER, UserRole.MODERATOR, UserRole.ADMINISTRATOR
)
require_moderator = require_roles(UserRole.MODERATOR, UserRole.ADMINISTRATOR)
require_admin = require_roles(UserRole.ADMINISTRATOR)

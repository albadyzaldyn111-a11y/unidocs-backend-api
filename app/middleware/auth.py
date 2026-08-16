"""
FastAPI dependencies enforcing authentication and RBAC.
This is the real security boundary — Flutter route guards are UX only.
"""
from dataclasses import dataclass

from fastapi import Depends, Header, Query
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
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    auth_token = None
    if authorization and authorization.lower().startswith("bearer "):
        auth_token = authorization.split(" ", 1)[1]
    elif token:
        auth_token = token

    if not auth_token:
        raise AppError("Authentication required", "UNAUTHENTICATED", 401)

    try:
        payload = decode_token(auth_token)
    except ValueError as exc:
        raise AppError("Invalid or expired token", "INVALID_TOKEN", 401) from exc

    user_id = payload.get("sub")
    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise AppError("User not found or inactive", "UNAUTHENTICATED", 401)

    return CurrentUser(id=user.id, role=user.role, university_id=user.university_id)


def get_optional_user(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser | None:
    """Same as get_current_user but returns None instead of raising —
    used for endpoints visitors may access anonymously while still
    attributing the action when a valid token is present (e.g. downloads)."""
    if not authorization and not token:
        return None
    try:
        return get_current_user(authorization=authorization, token=token, db=db)
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
require_uploader = require_roles(UserRole.VERIFIED_UPLOADER, UserRole.MODERATOR, UserRole.ADMINISTRATOR)
require_moderator = require_roles(UserRole.MODERATOR, UserRole.ADMINISTRATOR)
require_admin = require_roles(UserRole.ADMINISTRATOR)

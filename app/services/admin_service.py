from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import FileStatus, UserRole
from app.repositories.file_repository import FileRepository
from app.repositories.misc_repositories import SettingsRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.files = FileRepository(db)
        self.settings = SettingsRepository(db)
        self.audit = AuditService(db)

    def stats(self, university_id: str) -> dict:
        file_stats = self.files.stats(university_id)
        total_users = self.users.count_by_university(university_id)
        total_files = (
            file_stats["approved_files"]
            + file_stats["pending_files"]
            + file_stats["rejected_files"]
            + file_stats["archived_files"]
        )
        return {"total_users": total_users, "total_files": total_files, **file_stats}

    def set_user_active(self, admin_id: str, user_id: str, university_id: str, is_active: bool):
        user = self.users.get_by_id(user_id)
        if not user or user.university_id != university_id:
            raise AppError("User not found", "USER_NOT_FOUND", 404)
        user.is_active = is_active
        self.audit.log(admin_id, "DEACTIVATE_USER" if not is_active else "ACTIVATE_USER", "user", user.id)
        self.db.commit()
        return user

    def set_user_role(self, admin_id: str, user_id: str, university_id: str, role: UserRole):
        user = self.users.get_by_id(user_id)
        if not user or user.university_id != university_id:
            raise AppError("User not found", "USER_NOT_FOUND", 404)
        user.role = role
        self.audit.log(admin_id, "CHANGE_ROLE", "user", user.id, role.value)
        self.db.commit()
        return user

    def update_setting(self, admin_id: str, key: str, value: str):
        if key not in SettingsRepository.DEFAULTS:
            raise AppError("Unknown setting key", "UNKNOWN_SETTING", 404)
        self.settings.set(key, value)
        self.audit.log(admin_id, "CHANGE_SETTINGS", "setting", key, value)
        self.db.commit()

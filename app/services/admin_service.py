from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password
from app.models.enums import FileStatus, UserRole
from app.repositories.file_repository import FileRepository
from app.repositories.misc_repositories import SettingsRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.models.enums import NotificationType


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.files = FileRepository(db)
        self.settings = SettingsRepository(db)
        self.audit = AuditService(db)
        self.notifications = NotificationService(db)

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

    def _managed_user(self, user_id: str, university_id: str | None = None):
        user = self.users.get_by_id(user_id)
        if not user or (university_id is not None and user.university_id != university_id):
            raise AppError("User not found", "USER_NOT_FOUND", 404)
        return user

    def set_user_active(self, admin_id: str, user_id: str, university_id: str | None, is_active: bool):
        user = self._managed_user(user_id, university_id)
        user.is_active = is_active
        
        status_label = "تفعيل" if is_active else "تعطيل"
        self.notifications.notify(
            user.id,
            NotificationType.ACCOUNT_STATUS_CHANGED,
            f"تم {status_label} حسابك",
            f"قامت الإدارة بـ {status_label} حسابك في المنصة.",
            "user",
            user.id
        )
        
        self.audit.log(admin_id, "DEACTIVATE_USER" if not is_active else "ACTIVATE_USER", "user", user.id)
        self.db.commit()
        return user

    def set_user_role(self, admin_id: str, user_id: str, university_id: str | None, role: UserRole):
        user = self._managed_user(user_id, university_id)
        user.role = role
        
        role_labels = {
            UserRole.STUDENT: "طالب",
            UserRole.VERIFIED_UPLOADER: "رافع ملفات معتمد",
            UserRole.MODERATOR: "مشرف",
            UserRole.ADMINISTRATOR: "مسؤول نظام"
        }
        self.notifications.notify(
            user.id,
            NotificationType.ROLE_CHANGED,
            "تغيير رتبة الحساب",
            f"تم تغيير رتبة حسابك إلى: {role_labels.get(role, role.value)}",
            "user",
            user.id
        )
        
        self.audit.log(admin_id, "CHANGE_ROLE", "user", user.id, role.value)
        self.db.commit()
        return user

    def reset_user_password(self, admin_id: str, user_id: str, university_id: str | None, new_password: str):
        user = self._managed_user(user_id, university_id)
        user.password_hash = hash_password(new_password)
        self.audit.log(admin_id, "RESET_USER_PASSWORD", "user", user.id)
        self.db.commit()
        return {"success": True, "message": "Password reset successfully"}

    def update_setting(self, admin_id: str, key: str, value: str):
        if key not in SettingsRepository.DEFAULTS:
            raise AppError("Unknown setting key", "UNKNOWN_SETTING", 404)
        normalized = value.strip()
        boolean_keys = {
            "page_count_check_enabled",
            "email_notifications_enabled",
            "maintenance_mode",
            "notifications_new_files_enabled",
            "notifications_upload_status_enabled",
        }
        if key in boolean_keys and normalized.lower() not in {"true", "false"}:
            raise AppError("Setting must be true or false", "INVALID_SETTING_VALUE", 422)
        if key == "max_file_size_mb":
            try:
                size = int(normalized)
            except ValueError as exc:
                raise AppError("Maximum file size must be a number", "INVALID_SETTING_VALUE", 422) from exc
            if size < 1 or size > 1024:
                raise AppError("Maximum file size must be between 1 and 1024 MB", "INVALID_SETTING_VALUE", 422)
            normalized = str(size)
        if key == "allowed_extensions":
            media_extensions = {"png", "jpg", "jpeg", "gif", "webp", "svg", "mp3", "wav", "m4a", "mp4", "mov", "avi", "mkv"}
            extensions = [item.strip().lower().lstrip(".") for item in normalized.split(",") if item.strip()]
            if not extensions or any(item in media_extensions for item in extensions):
                raise AppError("Only document and text extensions are allowed", "INVALID_SETTING_VALUE", 422)
            normalized = ",".join(dict.fromkeys(extensions))
        if key in {"maintenance_message", "system_announcement"} and len(normalized) > 2000:
            raise AppError("Text setting is too long", "INVALID_SETTING_VALUE", 422)
        self.settings.set(key, normalized)
        self.audit.log(admin_id, "CHANGE_SETTINGS", "setting", key, normalized)
        self.db.commit()

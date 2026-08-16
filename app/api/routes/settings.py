from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.misc_repositories import SettingsRepository

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/public")
def public_settings(db: Session = Depends(get_db)):
    values = SettingsRepository(db).get_all()
    public_keys = (
        "maintenance_mode",
        "maintenance_message",
        "system_announcement",
        "max_file_size_mb",
        "allowed_extensions",
        "notifications_new_files_enabled",
        "notifications_upload_status_enabled",
    )
    return {key: values.get(key, "") for key in public_keys}

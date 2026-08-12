from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.middleware.auth import CurrentUser, get_current_user
from app.repositories.misc_repositories import NotificationRepository
from app.schemas.misc import NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return NotificationRepository(db).list_for_user(current_user.id)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    repo = NotificationRepository(db)
    notification = repo.get(notification_id, current_user.id)
    if not notification:
        raise AppError("Notification not found", "NOTIFICATION_NOT_FOUND", 404)
    notification.is_read = True
    db.commit()
    return notification


@router.post("/read-all")
def mark_all_read(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    NotificationRepository(db).mark_all_read(current_user.id)
    db.commit()
    return {"success": True, "message": "All notifications marked as read"}

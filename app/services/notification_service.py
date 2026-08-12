from sqlalchemy.orm import Session

from app.models.enums import NotificationType
from app.models.misc import Notification


class NotificationService:
    """In-app notifications today. The same call site will later be able to
    fan out to Push/Email backends without callers changing."""

    def __init__(self, db: Session):
        self.db = db

    def notify(
        self,
        user_id: str,
        type_: NotificationType,
        title: str,
        body: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type_,
            title=title,
            body=body,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        self.db.add(notification)
        self.db.flush()
        # Future: if settings.email_notifications_enabled -> EmailSender.send(...)
        # Future: PushSender.send(user_id, title, body)
        return notification

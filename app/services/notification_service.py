from sqlalchemy.orm import Session

from app.models.enums import NotificationType
from app.models.misc import Notification
from app.repositories.misc_repositories import SettingsRepository
from app.repositories.user_repository import UserRepository


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
        return notification

    def notify_university_users(
        self,
        university_id: str,
        type_: NotificationType,
        title: str,
        body: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        exclude_user_id: str | None = None,
    ) -> int:
        """Create inbox notifications for every active user in a university.

        This is the durable server-side event. Flutter can poll the inbox and
        surface each new row as a native notification without losing events.
        """
        if SettingsRepository(self.db).get("notifications_new_files_enabled").lower() != "true":
            return 0

        recipient_ids = UserRepository(self.db).active_ids_by_university(university_id)
        if exclude_user_id:
            recipient_ids = [user_id for user_id in recipient_ids if user_id != exclude_user_id]

        for recipient_id in recipient_ids:
            self.db.add(
                Notification(
                    user_id=recipient_id,
                    type=type_,
                    title=title,
                    body=body,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                )
            )
        self.db.flush()
        return len(recipient_ids)

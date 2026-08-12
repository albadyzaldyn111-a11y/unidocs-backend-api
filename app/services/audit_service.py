from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.misc import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, actor_id: str | None, action: str, entity_type: str, entity_id: str | None, details: str = ""):
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        self.db.flush()
        return entry

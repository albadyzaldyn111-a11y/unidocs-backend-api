from datetime import datetime

from pydantic import BaseModel

from app.models.enums import NotificationType, UploadRequestStatus


class UploadRequestCreate(BaseModel):
    reason: str | None = None


class UploadRequestOut(BaseModel):
    id: str
    user_id: str
    status: UploadRequestStatus
    reason: str | None
    review_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadRequestReview(BaseModel):
    note: str | None = None


class NotificationOut(BaseModel):
    id: str
    type: NotificationType
    title: str
    body: str | None
    is_read: bool
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminStatsOut(BaseModel):
    total_users: int
    total_files: int
    approved_files: int
    pending_files: int
    rejected_files: int
    archived_files: int
    total_downloads: int
    total_views: int


class SettingUpdate(BaseModel):
    value: str

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import NotificationType, UploadRequestStatus, UserRole
from app.repositories.misc_repositories import UploadRequestRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class UploadRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.requests = UploadRequestRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)
        self.notifications = NotificationService(db)

    def create(self, user_id: str, university_id: str, reason: str | None):
        if self.requests.has_pending(user_id):
            raise AppError("You already have a pending request", "REQUEST_PENDING", 409)
        req = self.requests.create(
            user_id=user_id, university_id=university_id, reason=reason, status=UploadRequestStatus.PENDING
        )
        self.audit.log(user_id, "CREATE_UPLOAD_REQUEST", "upload_request", req.id)
        self.db.commit()
        return req

    def approve(self, request_id: str, university_id: str, reviewer_id: str, note: str | None):
        req = self._get_or_404(request_id, university_id)
        if req.status != UploadRequestStatus.PENDING:
            raise AppError("Request already reviewed", "REQUEST_ALREADY_REVIEWED", 409)

        user = self.users.get_by_id(req.user_id)
        if user:
            # Promotion happens only in the backend — never trust the client.
            user.role = UserRole.VERIFIED_UPLOADER

        req.status = UploadRequestStatus.APPROVED
        req.reviewed_by = reviewer_id
        req.review_note = note

        self.notifications.notify(
            req.user_id,
            NotificationType.UPLOAD_REQUEST_APPROVED,
            "Upload request approved",
            "You are now a verified uploader.",
            "upload_request",
            req.id,
        )
        self.audit.log(reviewer_id, "APPROVE_UPLOAD_REQUEST", "upload_request", req.id)
        self.db.commit()
        return req

    def reject(self, request_id: str, university_id: str, reviewer_id: str, note: str | None):
        req = self._get_or_404(request_id, university_id)
        if req.status != UploadRequestStatus.PENDING:
            raise AppError("Request already reviewed", "REQUEST_ALREADY_REVIEWED", 409)

        req.status = UploadRequestStatus.REJECTED
        req.reviewed_by = reviewer_id
        req.review_note = note

        self.notifications.notify(
            req.user_id,
            NotificationType.UPLOAD_REQUEST_REJECTED,
            "Upload request rejected",
            note or "Your request was not approved.",
            "upload_request",
            req.id,
        )
        self.audit.log(reviewer_id, "REJECT_UPLOAD_REQUEST", "upload_request", req.id, note or "")
        self.db.commit()
        return req

    def _get_or_404(self, request_id: str, university_id: str):
        req = self.requests.get(request_id, university_id)
        if not req:
            raise AppError("Upload request not found", "REQUEST_NOT_FOUND", 404)
        return req

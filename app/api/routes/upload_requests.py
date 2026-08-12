from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.middleware.auth import CurrentUser, get_current_user, require_moderator, require_student_or_above
from app.repositories.misc_repositories import UploadRequestRepository
from app.schemas.misc import UploadRequestCreate, UploadRequestOut, UploadRequestReview
from app.services.upload_request_service import UploadRequestService

router = APIRouter(prefix="/api/requests", tags=["upload_requests"])


@router.post("", response_model=UploadRequestOut, status_code=201)
def create_request(
    payload: UploadRequestCreate,
    current_user: CurrentUser = Depends(require_student_or_above),
    db: Session = Depends(get_db),
):
    return UploadRequestService(db).create(current_user.id, current_user.university_id, payload.reason)


@router.get("", response_model=list[UploadRequestOut])
def list_requests(
    current_user: CurrentUser = Depends(require_moderator),
    db: Session = Depends(get_db),
):
    return UploadRequestRepository(db).list_by_university(current_user.university_id)


@router.get("/mine", response_model=list[UploadRequestOut])
def list_my_requests(
    current_user: CurrentUser = Depends(require_student_or_above),
    db: Session = Depends(get_db),
):
    # Declared before /{request_id} so "mine" is never swallowed as a path param.
    return UploadRequestRepository(db).list_by_user(current_user.id)


@router.get("/{request_id}", response_model=UploadRequestOut)
def get_request(
    request_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = UploadRequestRepository(db)
    req = repo.get(request_id, current_user.university_id)
    if not req:
        raise AppError("Request not found", "REQUEST_NOT_FOUND", 404)
    # A request is visible to the student who filed it, or to a moderator+.
    is_owner = req.user_id == current_user.id
    is_reviewer = current_user.role.value in ("moderator", "administrator")
    if not is_owner and not is_reviewer:
        raise AppError("You do not have permission to view this request", "FORBIDDEN", 403)
    return req


@router.post("/{request_id}/approve", response_model=UploadRequestOut)
def approve_request(
    request_id: str,
    payload: UploadRequestReview,
    current_user: CurrentUser = Depends(require_moderator),
    db: Session = Depends(get_db),
):
    return UploadRequestService(db).approve(request_id, current_user.university_id, current_user.id, payload.note)


@router.post("/{request_id}/reject", response_model=UploadRequestOut)
def reject_request(
    request_id: str,
    payload: UploadRequestReview,
    current_user: CurrentUser = Depends(require_moderator),
    db: Session = Depends(get_db),
):
    return UploadRequestService(db).reject(request_id, current_user.university_id, current_user.id, payload.note)

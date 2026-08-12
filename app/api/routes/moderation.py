from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import CurrentUser, require_moderator
from app.repositories.file_repository import FileRepository
from app.schemas.file import FileListItem, FileOut, RejectFileRequest
from app.services.file_service import FileService
from app.services.moderation_service import ModerationService

router = APIRouter(prefix="/api/moderation", tags=["moderation"])


@router.get("/files", response_model=list[FileListItem])
def list_pending(current_user: CurrentUser = Depends(require_moderator), db: Session = Depends(get_db)):
    items, _ = FileRepository(db).list_pending(current_user.university_id)
    return items


@router.get("/files/{file_id}/preview")
def preview_pending_file(
    file_id: str, current_user: CurrentUser = Depends(require_moderator), db: Session = Depends(get_db)
):
    service = FileService(db)
    file_obj = FileRepository(db).get(file_id, current_user.university_id)
    stream = service.open_stream(file_obj)
    return StreamingResponse(stream, media_type="application/pdf")


@router.post("/files/{file_id}/lock", response_model=FileOut)
def lock_file(file_id: str, current_user: CurrentUser = Depends(require_moderator), db: Session = Depends(get_db)):
    return ModerationService(db).lock(file_id, current_user.university_id, current_user.id)


@router.post("/files/{file_id}/approve", response_model=FileOut)
def approve_file(file_id: str, current_user: CurrentUser = Depends(require_moderator), db: Session = Depends(get_db)):
    return ModerationService(db).approve(file_id, current_user.university_id, current_user.id)


@router.post("/files/{file_id}/reject", response_model=FileOut)
def reject_file(
    file_id: str,
    payload: RejectFileRequest,
    current_user: CurrentUser = Depends(require_moderator),
    db: Session = Depends(get_db),
):
    return ModerationService(db).reject(file_id, current_user.university_id, current_user.id, payload.reason)


@router.delete("/files/{file_id}")
def delete_file(file_id: str, current_user: CurrentUser = Depends(require_moderator), db: Session = Depends(get_db)):
    ModerationService(db).delete(file_id, current_user.university_id, current_user.id)
    return {"success": True, "message": "File deleted"}

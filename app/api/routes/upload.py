from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.middleware.auth import CurrentUser, require_uploader
from app.middleware.rate_limit import limiter
from app.models.enums import FileStatus
from app.repositories.file_repository import FileRepository
from app.schemas.file import FileListItem, FileOut
from app.services.file_service import FileService

router = APIRouter(prefix="/api", tags=["upload"])
settings = get_settings()


@router.post("/files/upload", response_model=FileOut, status_code=201)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_file(
    request: Request,
    subject_id: str = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_uploader),
    db: Session = Depends(get_db),
):
    raw_bytes = await file.read()
    from app.models.taxonomy import Subject
    subject = db.get(Subject, subject_id)
    if not subject:
        from app.core.errors import AppError
        raise AppError("Subject not found", "SUBJECT_NOT_FOUND", 404)
        
    result = FileService(db).upload(
        uploader_id=current_user.id,
        university_id=subject.university_id,
        subject_id=subject_id,
        title=title,
        description=description,
        filename=file.filename or "upload",
        raw_bytes=raw_bytes,
        mime_type=file.content_type,
    )
    return result


@router.post("/files/{file_id}/versions", response_model=FileOut, status_code=201)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_new_version(
    request: Request,
    file_id: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_uploader),
    db: Session = Depends(get_db),
):
    raw_bytes = await file.read()
    from app.models.file import File as FileModel
    parent = db.get(FileModel, file_id)
    if not parent:
        from app.core.errors import AppError
        raise AppError("Original file not found", "FILE_NOT_FOUND", 404)

    result = FileService(db).upload_new_version(
        uploader_id=current_user.id,
        university_id=parent.university_id,
        parent_file_id=file_id,
        filename=file.filename or "upload",
        raw_bytes=raw_bytes,
        mime_type=file.content_type,
    )
    return result


@router.get("/files/mine/list", response_model=list[FileListItem])
def my_files(
    status: FileStatus | None = None,
    current_user: CurrentUser = Depends(require_uploader),
    db: Session = Depends(get_db),
):
    # Admins can see their uploads across all universities
    university_id = None if current_user.role == UserRole.ADMINISTRATOR else current_user.university_id
    return FileRepository(db).list_by_uploader(current_user.id, university_id, status)

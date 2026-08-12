import mimetypes
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.middleware.auth import CurrentUser, get_optional_user
from app.models.enums import FileStatus
from app.repositories.file_repository import FileRepository
from app.schemas.file import FileListItem, FileOut, PaginatedFiles
from app.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("", response_model=PaginatedFiles)
def search_files(
    university_id: str,
    q: str | None = None,
    subject_id: str | None = None,
    sort: str = "recent",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = FileRepository(db).search(
        university_id=university_id, q=q, subject_id=subject_id, sort=sort, page=page, limit=limit
    )
    return PaginatedFiles(
        items=[FileListItem.model_validate(i) for i in items], total=total, page=page, limit=limit
    )


@router.get("/{file_id}", response_model=FileOut)
def get_file(file_id: str, university_id: str, db: Session = Depends(get_db)):
    file_obj = FileRepository(db).get(file_id, university_id)
    if not file_obj or file_obj.status not in (FileStatus.APPROVED, FileStatus.ARCHIVED):
        raise AppError("File not found", "FILE_NOT_FOUND", 404)
    return file_obj


def _content_type(file_obj) -> str:
    return file_obj.mime_type or mimetypes.guess_type(file_obj.original_filename)[0] or "application/octet-stream"


def _content_disposition(filename: str, inline: bool) -> str:
    safe_name = filename.replace('"', "_").replace("\r", "_").replace("\n", "_")
    disposition = "inline" if inline else "attachment"
    return f"{disposition}; filename*=UTF-8''{quote(safe_name)}"


@router.get("/{file_id}/preview")
def preview_file(file_id: str, university_id: str, db: Session = Depends(get_db)):
    service = FileService(db)
    file_obj = service.register_view(file_id, university_id)
    stream = service.open_stream(file_obj)
    headers = {"Content-Disposition": _content_disposition(file_obj.original_filename, inline=True)}
    return StreamingResponse(stream, media_type=_content_type(file_obj), headers=headers)


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    university_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_user),
):
    service = FileService(db)
    file_obj = service.register_download(file_id, university_id, current_user.id if current_user else None)
    stream = service.open_stream(file_obj)
    headers = {"Content-Disposition": _content_disposition(file_obj.original_filename, inline=False)}
    return StreamingResponse(stream, media_type=_content_type(file_obj), headers=headers)

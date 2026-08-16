import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.middleware.auth import CurrentUser, get_current_user, get_optional_user
from app.models.enums import FileStatus
from app.repositories.file_repository import FileRepository
from app.schemas.file import FileListItem, FileOut, PaginatedFiles
from app.services.file_service import FileService

router = APIRouter(tags=["files"])


@router.get("", response_model=PaginatedFiles)
def search_files(
    university_id: str,
    q: str | None = None,
    subject_id: str | None = None,
    sort: str = "recent",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_user),
):
    items, total = FileRepository(db).search(
        university_id=university_id,
        q=q,
        subject_id=subject_id,
        sort=sort,
        page=page,
        limit=limit,
        include_pending_for_user=current_user.id if current_user else None,
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


@router.get("/{file_id}/preview")
def preview_file(
    file_id: str,
    university_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_user),
):
    service = FileService(db)
    file_obj = service.register_view(file_id, university_id, current_user.id if current_user else None)
    stream = service.open_stream(file_obj)
    return StreamingResponse(stream, media_type="application/pdf")


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
    
    extension = Path(file_obj.storage_key).suffix or ".bin"
    # Clean filename and handle non-latin characters for Content-Disposition
    from urllib.parse import quote
    
    base_filename = f"{file_obj.title}{extension}".replace('"', "").replace("\r", "").replace("\n", "")
    encoded_filename = quote(base_filename)
    
    media_type = mimetypes.guess_type(base_filename)[0] or "application/octet-stream"
    
    # Standard header with RFC 5987 support for UTF-8 filenames
    # We also provide a safe ASCII fallback filename for basic latin-1 compatibility
    safe_ascii_filename = base_filename.encode("ascii", "ignore").decode("ascii") or "file"
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    }
    return StreamingResponse(stream, media_type=media_type, headers=headers)

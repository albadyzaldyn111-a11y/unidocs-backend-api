from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.models.file import File
from app.models.misc import DownloadLog

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me/downloads")
def my_download_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(DownloadLog, File)
        .join(File, File.id == DownloadLog.file_id)
        .where(DownloadLog.user_id == current_user.id, DownloadLog.university_id == current_user.university_id)
        .order_by(DownloadLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "file_id": file.id,
            "title": file.title,
            "downloaded_at": log.created_at,
        }
        for log, file in rows
    ]

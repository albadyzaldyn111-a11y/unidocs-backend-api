from datetime import datetime

from pydantic import BaseModel

from app.models.enums import FileStatus


class FileOut(BaseModel):
    id: str
    university_id: str
    subject_id: str
    uploader_id: str
    title: str
    description: str | None
<<<<<<< HEAD
=======
    original_filename: str
    mime_type: str
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
    file_hash: str
    file_size_bytes: int
    status: FileStatus
    rejection_reason: str | None
    version_number: int
    parent_file_id: str | None
    downloads_count: int
    views_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileListItem(BaseModel):
    id: str
    title: str
<<<<<<< HEAD
=======
    original_filename: str
    mime_type: str
>>>>>>> 5a8a671 (Support arbitrary file uploads and academic taxonomy management)
    subject_id: str
    status: FileStatus
    file_size_bytes: int
    downloads_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedFiles(BaseModel):
    items: list[FileListItem]
    total: int
    page: int
    limit: int


class RejectFileRequest(BaseModel):
    reason: str

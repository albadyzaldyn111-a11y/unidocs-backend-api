import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    VERIFIED_UPLOADER = "verified_uploader"
    MODERATOR = "moderator"
    ADMINISTRATOR = "administrator"
    # "visitor" is not a stored role; it represents an unauthenticated caller.


class FileStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class UploadRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationType(str, enum.Enum):
    FILE_APPROVED = "file_approved"
    FILE_REJECTED = "file_rejected"
    UPLOAD_REQUEST_APPROVED = "upload_request_approved"
    UPLOAD_REQUEST_REJECTED = "upload_request_rejected"
    NEW_VERSION_APPROVED = "new_version_approved"
